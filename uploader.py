# uploader.py
import os
import pickle
import time
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from config import YOUTUBE_CLIENT_SECRETS_FILE

# --- Scopes & Token Path ---
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_PATH = os.path.join("config", "youtube_token.pickle")

def get_authenticated_service():
    """
    Handles OAuth 2.0 authorization.
    - Loads saved credentials if available.
    - Refreshes expired tokens automatically.
    - Prompts for login only the first time.
    """
    creds = None

    # Load existing token if it exists
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token_file:
            creds = pickle.load(token_file)

    # Refresh or initiate OAuth flow if necessary
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing YouTube credentials...")
            creds.refresh(Request())
        else:
            print("🔐 No valid credentials found. Please authorize access.")
            flow = InstalledAppFlow.from_client_secrets_file(
                YOUTUBE_CLIENT_SECRETS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the new credentials for future use
        os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
        with open(TOKEN_PATH, "wb") as token_file:
            pickle.dump(creds, token_file)

    return build("youtube", "v3", credentials=creds)


def upload_video(file_path, title, description="", tags=None, privacy="public"):
    """
    Uploads a video file to YouTube using the authorized credentials.

    Args:
        file_path (str): Path to the video file.
        title (str): Video title.
        description (str): Video description.
        tags (list[str]): List of tags.
        privacy (str): 'public', 'private', or 'unlisted'.

    Returns:
        dict: The YouTube API response (video metadata).
    """
    youtube = get_authenticated_service()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or ["shorts", "funny", "viral"],
            "categoryId": "23"  # 23 = Comedy
        },
        "status": {
            "privacyStatus": privacy
        }
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

    try:
        print(f"🚀 Starting upload: {title}")
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"⬆️ Upload progress: {int(status.progress() * 100)}%")
            time.sleep(0.2)

        print(f"✅ Upload complete! Video ID: {response['id']}")
        video_url = f"https://www.youtube.com/watch?v={response['id']}"
        print(f"📺 Watch here: {video_url}")
        return response

    except HttpError as e:
        print(f"❌ HTTP Error during upload: {e}")
        if e.resp.status in [500, 502, 503, 504]:
            print("🔁 Retrying upload due to server error...")
            time.sleep(5)
            return upload_video(file_path, title, description, tags, privacy)
        else:
            raise

    except Exception as e:
        print(f"⚠️ Upload failed: {e}")
        raise