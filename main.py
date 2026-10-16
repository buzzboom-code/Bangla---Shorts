import os
import asyncio
import subprocess
from groq import Groq
import edge_tts
from PIL import Image, ImageDraw, ImageFont

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

async def generate_bengali_script():
    prompt = """
    তুমি একজন বাংলা নিউজ শর্টস লেখক।
    বিশ্বের কোনো একটা সাম্প্রতিক গুরুত্বপূর্ণ নিউজ নিয়ে 
    ৩০-৪০ সেকেন্ডের জন্য একটি আকর্ষণীয় বাংলা শর্টস স্ক্রিপ্ট লেখো।
    শুরুতে শক্তিশালী হুক থাকতে হবে।
    শুধু স্ক্রিপ্টটাই লেখো, অন্য কিছু না।
    """
    
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "user", "content": prompt}
        ],
        model="openai/gpt-oss-20b",
    )
    
    script = chat_completion.choices[0].message.content.strip()
    print("Generated Script:")
    print(script)
    return script

async def generate_voice(script, output_file="voice.mp3"):
    voice = "bn-BD-PradeepNeural"
    communicate = edge_tts.Communicate(script, voice)
    await communicate.save(output_file)
    print(f"Voice saved as {output_file}")

def create_caption_image(script, output_image="caption.png"):
    print("Creating caption image with Pillow...")
    
    width, height = 1080, 1920
    img = Image.new("RGB", (width, height), color=(15, 15, 35))
    draw = ImageDraw.Draw(img)
    
    # ফন্ট খোঁজা
    possible_fonts = [
        "/usr/share/fonts/truetype/noto/NotoSansBengali-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansBengaliUI-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    
    font = None
    for path in possible_fonts:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, 44)
                print(f"Using font: {path}")
                break
            except:
                continue
    
    if font is None:
        font = ImageFont.load_default()
        print("Using default font")
    
    # টেক্সট লাইনে ভাগ করা
    words = script.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] < width - 100:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    # টেক্সট আঁকা
    line_height = 60
    total_text_height = len(lines) * line_height
    y = (height - total_text_height) // 2
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        
        # ছায়া
        draw.text((x+2, y+2), line, font=font, fill=(0, 0, 0))
        # মূল টেক্সট
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
        y += line_height
    
    img.save(output_image)
    print(f"Caption image saved as {output_image}")
    return output_image

def create_video(script, audio_file="voice.mp3", output_file="short.mp4"):
    caption_img = create_caption_image(script)
    
    print("Creating final video...")
    cmd = [
        "ffmpeg",
        "-y",
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