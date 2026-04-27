import imageio_ffmpeg
import subprocess

try:
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"FFMPEG EXE: {ffmpeg_exe}")
    result = subprocess.run([ffmpeg_exe, "-version"], capture_output=True, text=True)
    print("FFMPEG Version Output:")
    print(result.stdout)
except Exception as e:
    print(f"Error checking FFMPEG: {e}")
