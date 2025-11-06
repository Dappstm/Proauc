# editor.py
from moviepy.editor import VideoFileClip, CompositeVideoClip, concatenate_videoclips, TextClip
from moviepy.video.fx.all import resize, crop
from config import OUTPUT_DIR, MAX_TOTAL_DURATION, ALLOW_CROPPING
import os

def make_vertical_clip(video_path, target_width=1080, target_height=1920):
    clip = VideoFileClip(video_path)
    # convert to portrait 9:16 by cropping or padding
    w, h = clip.size
    # scale clip to fit width or height
    # we'll fit width to target_width and then crop/pad height
    factor = target_width / w
    clip = clip.resize(factor)
    # if now height less than target_height, center-pad (we'll use a black background)
    if clip.h < target_height:
        # create background clip and composite
        background = VideoFileClip(video_path).set_opacity(0)  # dummy to get duration
        background = background.set_duration(clip.duration)
    # if clip.h > target_height crop
    if clip.h > target_height:
        if ALLOW_CROPPING:
            clip = crop(clip, height=target_height, width=target_width, x_center=clip.w/2, y_center=clip.h/2)
        else:
            clip = clip.resize(height=target_height)
    clip = clip.set_position(("center","center"))
    clip = clip.resize((target_width, target_height))
    return clip

def label_clip(clip, label_text, corner="top-right", fontsize=40):
    # create a small text clip and overlay
    txt = TextClip(label_text, fontsize=fontsize, font="Arial-Bold", method="caption")
    txt = txt.with_duration(clip.duration)
    margin = 20
    if corner == "top-right":
        txt = txt.set_pos((clip.w - txt.w - margin, margin))
    elif corner == "top-left":
        txt = txt.set_pos((margin, margin))
    elif corner == "bottom-left":
        txt = txt.set_pos((margin, clip.h - txt.h - margin))
    elif corner == "bottom-right":
        txt = txt.set_pos((clip.w - txt.w - margin, clip.h - txt.h - margin))
    return CompositeVideoClip([clip, txt.set_start(0)])

def compose_short(clip_paths, labels, output_filename="final_short.mp4"):
    clips = []
    total = 0
    for i, p in enumerate(clip_paths):
        clip = VideoFileClip(p)
        # trim if too long per piece (give equal share)
        remaining = MAX_TOTAL_DURATION - total
        if remaining <= 0:
            break
        # naive: allow at most remaining, but keep each clip <= 15
        max_clip = min(15, remaining)
        if clip.duration > max_clip:
            clip = clip.subclip(0, max_clip)
        # convert/crop to vertical 9:16
        try:
            vclip = make_vertical_clip(p)
            labelled = label_clip(vclip, labels[i], corner="top-left")
            clips.append(labelled)
            total += labelled.duration
        except Exception as e:
            print("Error processing clip", p, e)
    if not clips:
        raise RuntimeError("No clips to compose")
    final = concatenate_videoclips(clips, method="compose")
    final = final.set_fps(24)
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    final.write_videofile(output_path, codec="libx264", audio_codec="aac", threads=4, preset="medium")
    return output_path
