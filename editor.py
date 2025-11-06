# editor.py
import os
from moviepy.editor import (
    VideoFileClip, CompositeVideoClip, concatenate_videoclips, TextClip
)
from moviepy.video.fx.all import crop
from config import OUTPUT_DIR, MAX_TOTAL_DURATION, ALLOW_CROPPING
from openai import OpenAI
import tempfile

client = OpenAI()

def extract_audio_transcript(video_path):
    """Extract audio from a clip and get its transcript using OpenAI Whisper."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_audio:
        # Extract audio
        clip = VideoFileClip(video_path)
        clip.audio.write_audiofile(tmp_audio.name, verbose=False, logger=None)
        clip.close()
        # Transcribe
        with open(tmp_audio.name, "rb") as f:
            transcription = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=f
            )
        os.remove(tmp_audio.name)
    return transcription.text.strip()

def make_vertical_clip(video_path, target_width=1080, target_height=1920):
    """Convert clip to portrait (9:16)."""
    clip = VideoFileClip(video_path)
    w, h = clip.size
    factor = target_width / w
    clip = clip.resize(factor)
    if clip.h > target_height:
        if ALLOW_CROPPING:
            clip = crop(
                clip, height=target_height, width=target_width,
                x_center=clip.w / 2, y_center=clip.h / 2
            )
        else:
            clip = clip.resize(height=target_height)
    clip = clip.set_position(("center", "center")).resize((target_width, target_height))
    return clip

def label_clip(clip, label_text, corner="top-left", fontsize=70, color="yellow", stroke_color="black"):
    """Add a bold label to one corner."""
    txt = TextClip(
        label_text,
        fontsize=fontsize,
        color=color,
        stroke_color=stroke_color,
        stroke_width=3,
        font="Arial-Bold",
        method="caption"
    ).set_duration(clip.duration)
    margin = 40
    if corner == "top-left":
        txt = txt.set_position((margin, margin))
    elif corner == "top-right":
        txt = txt.set_position((clip.w - txt.w - margin, margin))
    elif corner == "bottom-left":
        txt = txt.set_position((margin, clip.h - txt.h - margin))
    elif corner == "bottom-right":
        txt = txt.set_position((clip.w - txt.w - margin, clip.h - txt.h - margin))
    return CompositeVideoClip([clip, txt])

def compose_short(clip_paths, labels=None, output_filename="final_short.mp4"):
    """Combine multiple vertical clips into one video with top labels and AI-generated title."""
    transcripts = []
    clips = []
    total = 0

    print("🧠 Transcribing each clip for title generation...")
    for path in clip_paths:
        try:
            text = extract_audio_transcript(path)
            transcripts.append(text)
        except Exception as e:
            print(f"⚠️ Failed to transcribe {path}: {e}")
            transcripts.append("")

    # Generate short funny labels per clip
    prompt = (
        "You are a witty viral short video editor. "
        "Summarize each clip below in 2–4 funny, clickbait-style words. "
        "Number them from 1 to N. Only return the short titles.\n\n"
    )
    numbered_titles = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt + "\n\n".join(f"Clip {i+1}: {t}" for i, t in enumerate(transcripts))
    ).output_text.strip().splitlines()

    short_labels = [line.strip() for line in numbered_titles if line.strip()]

    # Generate main compilation title
    full_prompt = (
        "Based on these clips' transcripts, create one funny, clickbait YouTube Short title "
        "(like 'TOP 5 APPLE PAY PRANKS (GONE WRONG)'). Uppercase, max 10 words."
    )
    main_title = client.responses.create(
        model="gpt-4.1-mini",
        input=full_prompt + "\n\n" + "\n".join(transcripts)
    ).output_text.strip().upper()

    print(f"🎯 Generated main title: {main_title}")
    print("🎬 Building video...")

    # Build each vertical clip with its label
    for i, path in enumerate(clip_paths):
        clip = VideoFileClip(path)
        remaining = MAX_TOTAL_DURATION - total
        if remaining <= 0:
            break
        max_clip = min(15, remaining)
        if clip.duration > max_clip:
            clip = clip.subclip(0, max_clip)
        vclip = make_vertical_clip(path)
        label = short_labels[i] if i < len(short_labels) else f"CLIP {i+1}"
        labelled = label_clip(vclip, label_text=label, corner="top-left")
        clips.append(labelled)
        total += labelled.duration

    if not clips:
        raise RuntimeError("No valid clips to compose.")

    final = concatenate_videoclips(clips, method="compose").set_fps(24)

    # Add the main title at top center for first few seconds
    title_clip = TextClip(
        main_title,
        fontsize=100,
        color="yellow",
        stroke_color="black",
        stroke_width=5,
        font="Arial-Bold",
        method="caption"
    ).set_duration(3).set_position(("center", 100))

    final = CompositeVideoClip([final, title_clip])

    output_path = os.path.join(OUTPUT_DIR, output_filename)
    final.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="medium"
    )
    return output_path