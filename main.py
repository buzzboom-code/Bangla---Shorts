def create_video(script, audio_file="voice.mp3", output_file="short.mp4"):
    print("Creating vertical video with captions...")
    
    # টেক্সট ছোট লাইনে ভাগ করা
    words = script.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line + " " + word) < 22:
            current_line += " " + word if current_line else word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    caption_text = "\\n".join(lines)
    
    with open("caption.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    # সম্ভাব্য ফন্ট পাথগুলো চেষ্টা করা
    possible_fonts = [
        "/usr/share/fonts/truetype/noto/NotoSansBengali-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansBengaliUI-Regular.ttf",
        "/usr/share/fonts/truetype/lohit-bengali/Lohit-Bengali.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    
    font_path = None
    for path in possible_fonts:
        if os.path.exists(path):
            font_path = path
            print(f"Using font: {font_path}")
            break
    
    if not font_path:
        print("No suitable font found, using default")
        font_path = "Sans"
    
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", "color=c=#0f0f23:s=1080x1920:d=60",
        "-i", audio_file,
        "-vf", f"drawtext=fontfile={font_path}:textfile=caption.txt:fontcolor=white:fontsize=40:x=(w-text_w)/2:y=(h-text_h)/2:line_spacing=12:box=1:boxcolor=black@0.55:boxborderw=15",
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