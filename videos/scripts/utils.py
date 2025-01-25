import random

from moviepy import (
    AudioFileClip,
    VideoFileClip,
    TextClip,
    afx,
)
from PIL import Image
import pytesseract
import os
from django.conf import settings
from posts.models import Post

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
)

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
    elif media_type == "txt":
        posts = Post.objects.filter(
            subreddit__in=content_group.subreddits.all(),
            content__isnull=False,
            title__isnull=False,
        )
        media_field = "content"

    random_posts = random.sample(list(posts), content_group.media_per_video)

    if media_type != "txt":
        media_paths = [
            getattr(post, media_field).path
            for post in list(filter(lambda x: getattr(x, media_field), random_posts))
        ]

        if not len(media_paths):
            return False

        return media_paths, random_posts

    return [], random_posts


def create_text_clip(
    text, font_size=75, method="caption", duration=1.0, is_title=False
):
    if is_title:
        text_clip = TextClip(
            text=text,
            font=font_path,
            font_size=font_size,
            color="white",
            size=(VIDEO_WIDTH, VIDEO_HEIGHT),
            method=method,
            text_align="center",
            stroke_color="black",
            stroke_width=2,
            interline=10,
        )
        text_clip = text_clip.with_position("center")
    else:
        text_clip = TextClip(
            text=text,
            font=font_path,
            font_size=font_size,
            color="white",
            size=(VIDEO_WIDTH, VIDEO_HEIGHT),
            method=method,
            text_align="center",
            stroke_color="black",
            stroke_width=2,
            interline=8,
        )
        text_clip = text_clip.with_position("center")

    text_clip = text_clip.with_duration(duration)
    return text_clip


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


def add_audio_to_clip(clip, audio):
    audio_clip = AudioFileClip(audio)

    if clip.duration > audio_clip.duration:
        audio_clip = audio_clip.with_effects([afx.AudioLoop(duration=clip.duration)])
    else:
        audio_clip = audio_clip.subclipped(0, clip.duration)

    clip = clip.with_audio(audio_clip)
    return clip
