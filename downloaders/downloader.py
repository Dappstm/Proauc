# downloaders/downloader.py
import os
from config import DOWNLOAD_DIR
import subprocess
import shlex
import uuid

def download_with_ytdlp(url, filename_prefix="clip"):
    """
    Use yt-dlp to robustly download video (supports reddit, youtube, tiktok, twitter links).
    Returns path to downloaded file.
    """
    outname = os.path.join(DOWNLOAD_DIR, f"{filename_prefix}_{uuid.uuid4().hex}.%(ext)s")
    cmd = f"yt-dlp -f best -o {shlex.quote(outname)} {shlex.quote(url)}"
    print("Running:", cmd)
    subprocess.check_call(cmd, shell=True)
    # find the file created (yt-dlp expands extension)
    # return the first matching file
    base = outname.split("%")[0]
    for f in os.listdir(DOWNLOAD_DIR):
        if f.startswith(os.path.basename(base)):
            return os.path.join(DOWNLOAD_DIR, f)
    raise FileNotFoundError("Downloaded file not found")
