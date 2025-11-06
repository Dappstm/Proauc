# fetchers/youtube_fetcher.py
from googleapiclient.discovery import build
from config import YOUTUBE_CLIENT_SECRETS_FILE
import os

# For searching YouTube (needs API key from Google Cloud). Simpler approach: use API key and 'youtube' build.
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def search_youtube_short_videos(q="funny cringe short", max_results=25):
    if not YOUTUBE_API_KEY:
        return []
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    req = youtube.search().list(part="snippet", q=q, type="video", videoDuration="short", maxResults=max_results)
    res = req.execute()
    items = []
    for it in res.get("items", []):
        items.append({
            "title": it["snippet"]["title"],
            "videoId": it["id"]["videoId"],
            "url": f"https://www.youtube.com/watch?v={it['id']['videoId']}",
            "source":"youtube"
        })
    return items
