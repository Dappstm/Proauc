# fetchers/youtube_fetcher.py
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
from config import YOUTUBE_CLIENT_SECRETS_FILE
import os
import re

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def parse_iso_duration(duration_str):
    """
    Convert ISO 8601 duration (e.g., PT45S, PT1M2S) to seconds.
    """
    match = re.match(
        r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_str
    )
    if not match:
        return 0
    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0
    return hours * 3600 + minutes * 60 + seconds

def search_youtube_short_videos(
    tags=("short", "funny", "viral"),
    max_results=50,
    max_total_duration=58,
    min_clips=4,
    max_clips=8
):
    """
    Search for recent short YouTube videos with specific tags,
    not older than 1 month, and ensure that the total of selected clips
    can fit within 58 seconds without trimming.
    """
    if not YOUTUBE_API_KEY:
        print("⚠️ Missing YOUTUBE_API_KEY in environment variables.")
        return []

    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    # Calculate date 1 month ago (in ISO format)
    published_after = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

    # Build combined search query
    query = " ".join(tags)

    # 1️⃣ Search for short videos published within the last month
    search_req = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        videoDuration="short",
        publishedAfter=published_after,
        maxResults=max_results
    )
    search_res = search_req.execute()

    video_ids = [item["id"]["videoId"] for item in search_res.get("items", [])]

    if not video_ids:
        print("⚠️ No search results found.")
        return []

    # 2️⃣ Get full video details (including duration)
    video_req = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        id=",".join(video_ids)
    )
    video_res = video_req.execute()

    # 3️⃣ Filter and format results
    items = []
    for vid in video_res.get("items", []):
        title = vid["snippet"]["title"]
        video_id = vid["id"]
        duration = parse_iso_duration(vid["contentDetails"]["duration"])
        tags_in_video = vid["snippet"].get("tags", [])
        published = vid["snippet"]["publishedAt"]

        # Only include if within 1 month and tags match desired keywords
        if duration == 0 or duration > 58:
            continue

        # ensure it has at least one keyword in title or tags
        title_lower = title.lower()
        if not any(tag.lower() in title_lower or tag.lower() in (", ".join(tags_in_video)).lower() for tag in tags):
            continue

        items.append({
            "title": title,
            "videoId": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "duration": duration,
            "publishedAt": published,
            "source": "youtube"
        })

    # 4️⃣ Ensure the total duration of chosen 4–8 clips ≤ 58s
    items.sort(key=lambda x: x["duration"])  # shortest first
    valid_sets = []
    for n in range(min_clips, max_clips + 1):
        total = 0
        selection = []
        for v in items:
            if total + v["duration"] <= max_total_duration:
                selection.append(v)
                total += v["duration"]
                if len(selection) == n:
                    break
        if len(selection) == n:
            valid_sets.append(selection)

    if not valid_sets:
        print("⚠️ Could not find enough clips to fit under total duration limit.")
        return []

    # Return one random valid set
    import random
    chosen = random.choice(valid_sets)
    print(f"✅ Selected {len(chosen)} YouTube clips totaling {sum(v['duration'] for v in chosen)}s")
    return chosen