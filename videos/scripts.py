import os
import random
import datetime
import pytesseract
import numpy as np
import tempfile

from moviepy import (
    ImageClip,
    AudioFileClip,
    TextClip,
    VideoFileClip,
    CompositeVideoClip,
    concatenate_videoclips,
    afx,
)

from django.core.files import File
from django.utils import timezone
from PIL import Image
from django.conf import settings

from posts.models import Post
from videos.models import GeneratedVideo

audio_path = os.path.join(settings.MEDIA_ROOT, "audio\\meme\\edamame.mp3")
minecraft_path = os.path.join(settings.MEDIA_ROOT, "backgrounds\\minecraft")
subway_path = os.path.join(settings.MEDIA_ROOT, "backgrounds\\minecraft")
font_path = os.path.join(settings.MEDIA_ROOT, "font.otf")

minecraft_files = [
    f"{minecraft_path}\\{f}"
    for f in os.listdir(minecraft_path)
    if os.path.isfile(os.path.join(minecraft_path, f))
]

subway_files = [
    f"{subway_path}\\{f}"
    for f in os.listdir(subway_path)
    if os.path.isfile(os.path.join(subway_path, f))
]

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
)


def generate_video(content_group):
    if content_group.type == "img":
        return generate_media_video(content_group, media_type="img")
    elif content_group.type == "vid":
        return generate_media_video(content_group, media_type="vid")
    elif content_group.type == "text":
        return generate_text_video(content_group)
    raise ValueError("Invalid content group type.")


def find_words_in_image(image_path):
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)

    words = list(map(lambda x: x.split(" "), text.split("\n")))
    words_flat = [word for line in words for word in line]
    words_qty = len(list(filter(lambda x: x.strip() != "", words_flat)))

    return words_qty


def get_background(background_type):
    if background_type == "black":
        return Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0))
    elif background_type in ["minecraft", "subway"]:
        video = random.choice(
            minecraft_files if background_type == "minecraft" else subway_files
        )
        return VideoFileClip(video)
    return get_background("minecraft" if random.random() < 0.5 else "subway")


def find_duration(image_path):
    words = find_words_in_image(image_path) - 10
    duration = 5

    if words > 0:
        duration += words / 6

    return duration


def get_media(content_group, media_type):
    if media_type == "img":
        posts = Post.objects.filter(
            subreddit__in=content_group.subreddits.all(), image__isnull=False
        )
        media_field = "image"
    elif media_type == "vid":
        posts = Post.objects.filter(
            subreddit__in=content_group.subreddits.all(), video__isnull=False
        )
        media_field = "video"
    else:
        raise ValueError("Invalid media type. Use 'img' or 'vid'.")

    random_posts = random.sample(list(posts), content_group.media_per_video)

    media_paths = [
        getattr(post, media_field).path
        for post in list(filter(lambda x: getattr(x, media_field), random_posts))
    ]

    if not len(media_paths):
        return False

    return media_paths, random_posts


def resize_media(media_path, target_size=(VIDEO_WIDTH, VIDEO_HEIGHT), media_type="img"):
    if media_type == "img":
        img = Image.open(media_path)

        target_width, target_height = target_size

        img.thumbnail(
            (target_width * 0.8, target_height * 0.4), Image.Resampling.LANCZOS
        )

        return img
    elif media_type == "vid":
        video_clip = VideoFileClip(media_path)

        aspect_ratio = video_clip.size[0] / video_clip.size[1]
        if aspect_ratio > (target_size[0] / target_size[1]):
            new_width = int(target_size[0] * 0.8)
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = int(target_size[1] * 0.4)
            new_width = int(new_height * aspect_ratio)

        resized_clip = video_clip.resized((new_width, new_height))

        return resized_clip
    else:
        raise ValueError("Invalid media type. Use 'img' or 'vid'.")


def create_canvas_with_media(
    media_paths, media_type="img", canvas_width=1080, canvas_height=1920
):
    if media_type == "img":
        canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))

        for index, path in enumerate(media_paths):
            img = resize_media(path)

            if img.mode != "RGBA":
                img = img.convert("RGBA")

            x = (canvas_width - img.width) // 2
            if index == 0:
                y = int(0.05 * canvas_height)
            else:
                y = int(0.55 * canvas_height)

            canvas.paste(img, (x, y), img)

        canvas_np = np.array(canvas)
        return canvas_np
    elif media_type == "vid":
        max_duration = max(
            [
                resize_media(video_path, media_type="vid").duration
                for video_path in media_paths
            ]
        )
        canvas_clip = ImageClip(
            np.zeros((canvas_height, canvas_width, 4), dtype=np.uint8)
        ).with_duration(max_duration)

        video_clips_with_positions = []

        for index, video_path in enumerate(media_paths):
            resized_clip = resize_media(video_path, media_type="vid")

            x = (canvas_width - resized_clip.size[0]) // 2
            if len(media_paths) == 1:
                y = (canvas_height - resized_clip.size[1]) // 2
            else:
                if index == 0:
                    y = int(0.05 * canvas_height)
                else:
                    y = int(0.55 * canvas_height)

            video_clips_with_positions.append(resized_clip.with_position((x, y)))

        composite_clip = CompositeVideoClip([canvas_clip] + video_clips_with_positions)

        return composite_clip
    else:
        raise ValueError("Invalid media type. Use 'img' or 'vid'.")


def add_audio_to_clip(clip, audio):
    audio_clip = AudioFileClip(audio)

    if clip.duration > audio_clip.duration:
        audio_clip = audio_clip.with_effects([afx.AudioLoop(duration=clip.duration)])
    else:
        audio_clip = audio_clip.subclipped(0, clip.duration)

    clip = clip.with_audio(audio_clip)
    return clip


def create_text_clip(text, duration=1.0):
    text_clip = TextClip(
        font=font_path,
        text=text,
        font_size=100,
        color="white",
        size=(VIDEO_WIDTH, VIDEO_HEIGHT),
    )
    text_clip = text_clip.with_position("center")
    text_clip = text_clip.with_duration(duration)

    return text_clip


def generate_media_video(content_group, media_type="img"):
    media_result = get_media(content_group, media_type)
    if not media_result:
        print("No media found for the content group.")
        return

    media_paths, posts = media_result

    temp_video_path = f"temp_video_{int(datetime.datetime.now().timestamp())}.mp4"
    fps = 10

    background_clip = get_background(content_group.background)

    overlay_clips = []

    if content_group.start_text:
        text_clip = create_text_clip(content_group.start_text)
        overlay_clips.append(text_clip)

    media_per_screen = content_group.media_per_screen
    for i in range(0, len(media_paths), media_per_screen):
        screen_media = media_paths[i : i + media_per_screen]

        if media_type == "img":
            canvas_np = create_canvas_with_media(screen_media, media_type="img")
            media_clip = ImageClip(canvas_np).with_duration(
                sum([find_duration(img) for img in screen_media])
            )
        elif media_type == "vid":
            media_clip = create_canvas_with_media(screen_media, media_type="vid")

        overlay_clips.append(media_clip)

    if content_group.end_text:
        text_clip = create_text_clip(content_group.end_text)
        overlay_clips.append(text_clip)

    overlay_clip = concatenate_videoclips(overlay_clips)

    if background_clip.duration < overlay_clip.duration:
        background_clip = background_clip.loop(duration=overlay_clip.duration)
    else:
        background_clip = background_clip.subclipped(0, overlay_clip.duration)

    final_clip = CompositeVideoClip([background_clip, overlay_clip])
    final_clip = add_audio_to_clip(final_clip, audio_path)

    final_clip.write_videofile(temp_video_path, codec="libx264", fps=fps)

    metadata = {
        "length": float(final_clip.duration),
        "background": content_group.background,
        "media_per_screen": content_group.media_per_screen,
        "media_qty": len(posts),
        "video_type": content_group.type,
        "start_text": content_group.start_text,
        "end_text": content_group.end_text,
    }

    with open(temp_video_path, "rb") as video_file:
        video_content = File(video_file)
        generated_video = GeneratedVideo.objects.create(
            video=video_content,
            content_group=content_group,
            created_at=timezone.now(),
            meta_data=metadata,
        )
        generated_video.used_media.set(posts)

    os.remove(temp_video_path)


def generate_text_video(content_group):
    """
    Generate a video using text (to be implemented).
    """
    pass
