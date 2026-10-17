import os
import asyncio
import subprocess
import requests
from groq import Groq
import edge_tts
from PIL import Image, ImageDraw, ImageFont

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
UNSPLASH_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")

def clean_for_tts(text):
    text = text.replace(" সালে", " এ")
    text = text.replace(" সালের", " এর")
    text = text.replace(" সাল", "")
    text = text.replace("সাল ", "")
    return text.strip()

def clean_for_display(text):
    replacements = {
        "GPT-5": "জিপিটি ফাইভ",
        "GPT-4": "জিপিটি ফোর",
        "ChatGPT": "চ্যাটজিপিটি",
        "OpenAI": "ওপেনএআই",
        "AI": "এআই",
        "Google": "গুগল",
        "Microsoft": "মাইক্রোসফট",
        "Meta": "মেটা",
        "Apple": "অ্যাপল",
    }
    for eng, ban in replacements.items():
        text = text.replace(eng, ban)
        text = text.replace(eng.lower(), ban)
    return text

async def generate_script():
    prompt = """তুমি একজন পেশাদার বাংলা নিউজ শর্টস লেখক।
বিশ্বের একটি সাম্প্রতিক গুরুত্বপূর্ণ খবর নিয়ে ৩৫ সেকেন্ডের আকর্ষণীয় বাংলা স্ক্রিপ্ট লেখো।
নিয়ম:
- শুধু বাংলায় লিখবে
- ইংরেজি শব্দ একেবারেই ব্যবহার করবে না
- শুরুতে শক্তিশালী হুক থাকবে
- শুধু স্ক্রিপ্ট লিখবে, অন্য কিছু না"""

    for i in range(3):
        try:
            res = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="openai/gpt-oss-20b",
                temperature=0.85,
            )
            script = res.choices[0].message.content.strip()
            if script and len(script) > 80:
                print("Generated Script:")
                print(script)
                return script
            print(f"Attempt {i+1}: script too short, retrying...")
        except Exception as e:
            print(f"Attempt {i+1} error: {e}")

    return "আজকের গুরুত্বপূর্ণ খবর। বিশ্বজুড়ে বড় পরিবর্তন ঘটছে। বিস্তারিত জানতে আমাদের চ্যানেল সাবস্ক্রাইব করুন।"

async def generate_voice(script, filename="voice.mp3"):
    cleaned = clean_for_tts(script)
    print("TTS Script:", cleaned)

    voices = ["bn-BD-PradeepNeural", "bn-IN-BashkarNeural", "bn-BD-NabanitaNeural"]
    
    for voice in voices:
        try:
            communicate = edge_tts.Communicate(cleaned, voice)
            await communicate.save(filename)
            if os.path.exists(filename) and os.path.getsize(filename) > 1000:
                print(f"Voice saved successfully with {voice}")
                return
        except Exception as e:
            print(f"Voice {voice} failed: {e}")

    raise Exception("All voices failed")

def get_keywords(script):
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": f"Extract 3 English keywords for image search from this text. Reply only keywords:\n{script}"}],
            model="openai/gpt-oss-20b",
        )
        kw = res.choices[0].message.content.strip()
        print("Keywords:", kw)
        return kw
    except:
        return "news world technology"

def download_bg(keywords):
    if not UNSPLASH_KEY:
        return None
    try:
        headers = {"Authorization": f"Client-ID {UNSPLASH_KEY}"}
        r = requests.get("https://api.unsplash.com/search/photos", 
                         headers=headers, 
                         params={"query": keywords, "orientation": "portrait", "per_page": 1},
                         timeout=12)
        if r.status_code == 200 and r.json().get("results"):
            url = r.json()["results"][0]["urls"]["regular"]
            data = requests.get(url, timeout=12).content
            with open("bg.jpg", "wb") as f:
                f.write(data)
            print("Background downloaded")
            return "bg.jpg"
    except Exception as e:
        print("Background error:", e)
    return None

def create_image(script, bg=None):
    script = clean_for_display(script)
    width, height = 1080, 1920

    if bg and os.path.exists(bg):
        img = Image.open(bg).convert("RGB").resize((width, height))
        dark = Image.new("RGB", (width, height), (0, 0, 0))
        img = Image.blend(img, dark, 0.42)
    else:
        img = Image.new("RGB", (width, height), (12, 12, 30))

    draw = ImageDraw.Draw(img)

    font = None
    for path in ["fonts/NotoSansBengali-Regular.ttf", "fonts/NotoSansBengali-Bold.ttf"]:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, 40)
                break
            except:
                pass
    if font is None:
        font = ImageFont.load_default()

    words = script.split()
    lines, current = [], ""
    for w in words:
        test = current + " " + w if current else w
        if draw.textbbox((0, 0), test, font=font)[2] < width - 70:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)

    y = (height - len(lines) * 55) // 2
    for line in lines:
        tw = draw.textbbox((0, 0), line, font=font)[2]
        x = (width - tw) // 2
        draw.text((x+2, y+2), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
        y += 55

    img.save("caption.png")
    print("Caption image created")
    return "caption.png"

def make_video():
    if not os.path.exists("voice.mp3") or os.path.getsize("voice.mp3") < 1000:
        raise Exception("Invalid voice file")

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", "caption.png",
        "-i", "voice.mp3",
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p", "-shortest",
        "-vf", "scale=1080:1920",
        "short.mp4"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr)
        raise Exception("FFmpeg failed")
    print("Video created successfully")

async def main():
    print("Starting...")
    script = await generate_script()
    
    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(script)

    await generate_voice(script)
    
    keywords = get_keywords(script)
    bg = download_bg(keywords)
    create_image(script, bg)
    make_video()
    
    print("All done!")

if __name__ == "__main__":
    asyncio.run(main())