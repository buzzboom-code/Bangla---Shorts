import os
import asyncio
import subprocess
import requests
from groq import Groq
import edge_tts
from PIL import Image, ImageDraw, ImageFont

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
UNSPLASH_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")

async def generate_bengali_script():
    prompt = """
    তুমি একজন বাংলা নিউজ শর্টস লেখক।
    বিশ্বের কোনো একটা সাম্প্রতিক গুরুত্বপূর্ণ নিউজ নিয়ে 
    ৩০-৪০ সেকেন্ডের জন্য একটি আকর্ষণীয় বাংলা শর্টস স্ক্রিপ্ট লেখো।
    শুরুতে শক্তিশালী হুক থাকতে হবে।
    শুধু স্ক্রিপ্টটাই লেখো, অন্য কিছু না।
    """
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="openai/gpt-oss-20b",
    )
    
    script = chat_completion.choices[0].message.content.strip()
    print("Generated Script:")
    print(script)
    return script
def clean_script_for_tts(script):
    """সাল শব্দ সরিয়ে উচ্চারণ ঠিক করা"""
    script = script.replace(" সালে", " এ")
    script = script.replace(" সালের", " এর")
    script = script.replace(" সাল", "")
    script = script.replace("সাল ", "")
    return script

async def generate_voice(script, output_file="voice.mp3"):
    voice = "bn-BD-PradeepNeural"
    cleaned = clean_script_for_tts(script)
    print("TTS Script:", cleaned)
    communicate = edge_tts.Communicate(cleaned, voice)

def get_keyword(script):
    """স্ক্রিপ্ট থেকে ইংরেজি কীওয়ার্ড বের করা"""
    prompt = f"From this Bengali news script, extract 2-3 English keywords for image search. Reply only the keywords separated by space:\n\n{script}"
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="openai/gpt-oss-20b",
    )
    keywords = chat_completion.choices[0].message.content.strip()
    print(f"Keywords: {keywords}")
    return keywords

def download_background(keywords, output_file="bg.jpg"):
    print(f"Searching Unsplash for: {keywords}")
    
    headers = {"Authorization": f"Client-ID {UNSPLASH_KEY}"}
    params = {
        "query": keywords,
        "orientation": "portrait",
        "per_page": 1
    }
    
    response = requests.get("https://api.unsplash.com/search/photos", headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data["results"]:
            img_url = data["results"][0]["urls"]["regular"]
            img_data = requests.get(img_url).content
            with open(output_file, "wb") as f:
                f.write(img_data)
            print(f"Background downloaded: {output_file}")
            return output_file
    
    print("No image found, using solid color")
    return None

def create_caption_image(script, bg_image=None, output_image="caption.png"):
    print("Creating caption image...")
    
    width, height = 1080, 1920
    
    if bg_image and os.path.exists(bg_image):
        img = Image.open(bg_image).convert("RGB")
        img = img.resize((width, height))
        # একটু ডার্ক করে টেক্সট পড়ার সুবিধা
        overlay = Image.new("RGB", (width, height), (0, 0, 0))
        img = Image.blend(img, overlay, 0.45)
    else:
        img = Image.new("RGB", (width, height), color=(15, 15, 35))
    
    draw = ImageDraw.Draw(img)
    
    possible_fonts = [
        "fonts/NotoSansBengali-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansBengali-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    
    font = None
    for path in possible_fonts:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, 42)
                print(f"Using font: {path}")
                break
            except:
                continue
    if font is None:
        font = ImageFont.load_default()
    
    words = script.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] < width - 80:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    line_height = 58
    total_text_height = len(lines) * line_height
    y = (height - total_text_height) // 2
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        
        draw.text((x+2, y+2), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
        y += line_height
    
    img.save(output_image)
    print(f"Caption image saved")
    return output_image

def create_video(script, audio_file="voice.mp3", output_file="short.mp4"):
    keywords = get_keyword(script)
    bg = download_background(keywords)
    caption_img = create_caption_image(script, bg)
    
    print("Creating final video...")
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", caption_img,
        "-i", audio_file,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "-vf", "scale=1080:1920",
        output_file
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFmpeg Error:")
        print(result.stderr)
        raise Exception("Video creation failed")
    
    print(f"Video saved as {output_file}")

async def main():
    print("Starting Bengali Shorts generation...")
    
    script = await generate_bengali_script()
    
    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(script)
    
    await generate_voice(script)
    create_video(script)
    
    print("Done! script.txt, voice.mp3 and short.mp4 created.")

if __name__ == "__main__":
    asyncio.run(main())