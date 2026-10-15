import os
import asyncio
import subprocess
from groq import Groq
import edge_tts

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

def create_video(script, audio_file="voice.mp3", output_file="short.mp4"):
    print("Creating vertical video with captions...")
    
    # টেক্সট ছোট ছোট লাইনে ভাগ করা
    words = script.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line + " " + word) < 25:
            current_line += " " + word if current_line else word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    caption_text = "\n".join(lines)
    
    with open("caption.txt", "w", encoding="utf-8") as f:
        f.write(caption_text)
    
    # ফন্ট খুঁজে বের করা
    font_path = "/usr/share/fonts/truetype/noto/NotoSansBengali-Regular.ttf"
    
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", "color=c=#1a1a2e:s=1080x1920:d=60",
        "-i", audio_file,
        "-vf", f"drawtext=fontfile={font_path}:textfile=caption.txt:fontcolor=white:fontsize=42:x=(w-text_w)/2:y=(h-text_h)/2:line_spacing=15:box=1:boxcolor=black@0.6:boxborderw=20",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_file
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFmpeg Error:")
        print(result.stderr)
        raise Exception("Video creation failed")
    
    print(f"Video saved as {output_file}")
    print("Creating vertical video with captions...")
    
    # স্ক্রিপ্টকে টেক্সট ফাইলে সেভ করা
    with open("caption.txt", "w", encoding="utf-8") as f:
        f.write(script)
    
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", "color=c=black:s=1080x1920:d=60",
        "-i", audio_file,
        "-vf", "drawtext=fontfile=/usr/share/fonts/truetype/noto/NotoSansBengali-Regular.ttf:textfile=caption.txt:fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=black@0.5:boxborderw=10",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_file
    ]
    
    subprocess.run(cmd, check=True)
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