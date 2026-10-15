import os
import asyncio
from groq import Groq
import edge_tts

# Groq client
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
    # বাংলা ভয়েস (বাংলাদেশ)
    voice = "bn-BD-PradeeNeural"
    
    communicate = edge_tts.Communicate(script, voice)
    await communicate.save(output_file)
    print(f"Voice saved as {output_file}")

async def main():
    print("Starting Bengali Shorts generation...")
    
    script = await generate_bengali_script()
    
    # স্ক্রিপ্ট সেভ করা
    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(script)
    
    # ভয়েস জেনারেট করা
    await generate_voice(script)
    
    print("Done! script.txt and voice.mp3 created.")

if __name__ == "__main__":
    asyncio.run(main())