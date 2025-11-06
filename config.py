import os

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Limits
MIN_CLIPS = 4
MAX_CLIPS = 8
MAX_TOTAL_DURATION = 58  # seconds for YouTube Shorts safety

# API keys - load from environment or .env
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "shorts-bot/0.1")

YOUTUBE_CLIENT_SECRETS_FILE = os.getenv("YOUTUBE_CLIENT_SECRETS_FILE")  # path to client_secrets.json
YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN")  # optional if using OAuth flow

TWITTER_BEARER = os.getenv("TWITTER_BEARER")
TIKTOK_COOKIE = os.getenv("TIKTOK_COOKIE")  # if needed by TikTokApi

# Safety / policy
ALLOW_CROPPING = True  # crop to 9:16 if needed
