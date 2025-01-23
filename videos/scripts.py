import os
import random
import datetime
import pytesseract
import tempfile
import numpy as np

from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    TextClip,
    VideoFileClip,
    CompositeVideoClip,
    concatenate_videoclips,
)
from moviepy.config import change_settings
from moviepy.audio.fx.all import audio_loop

from django.core.files import File
from django.utils import timezone
from PIL import Image
from io import BytesIO
from django.conf import settings

from posts.models import Post
from videos.models import GeneratedVideo

audio_path = os.path.join(settings.MEDIA_ROOT, "audio\\meme\\edamame.mp3")
minecraft_path = os.path.join(settings.MEDIA_ROOT, "backgrounds\\minecraft")
subway_path = os.path.join(settings.MEDIA_ROOT, "backgrounds\\minecraft")

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

change_settings(
    {"IMAGEMAGICK_BINARY": r"C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"}
)
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
)


def generate_video(content_group):
    if content_group.type == "img":
        return generate_images_video(content_group)
    elif content_group.type == "vid":
        return generate_videos_video(content_group)
    elif content_group.type == "text":
        return generate_text_video(content_group)
    raise ValueError(
        "Content group type is wrong, achieved unachieveable piece of code."
    )


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


def resize_image(image_path, target_size=(VIDEO_WIDTH, VIDEO_HEIGHT)):
    img = Image.open(image_path)

    target_width, target_height = target_size

    img.thumbnail((target_width * 0.8, target_height * 0.4), Image.Resampling.LANCZOS)

    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format="PNG", quality=100)
    img_byte_arr.seek(0)

    return img_byte_arr


def get_images(content_group):
    posts = Post.objects.filter(
        subreddit__in=content_group.subreddits.all(), image__isnull=False
    )

    random_posts = random.sample(list(posts), content_group.media_per_video)

    image_paths = [
        post.image.path for post in list(filter(lambda x: x.image, random_posts))
    ]

    if not len(image_paths):
        return False

    resized_images = [resize_image(img_path) for img_path in image_paths]

    temp_resized_image_paths = []

    for i, resized_img in enumerate(resized_images):
        temp_image_path = f"temp_image_{i}.png"
        with open(temp_image_path, "wb") as temp_image_file:
            temp_image_file.write(resized_img.getvalue())
        temp_resized_image_paths.append(temp_image_path)

    return temp_resized_image_paths, random_posts


def add_audio_to_clip(clip, audio):
    audio_clip = AudioFileClip(audio)

    if clip.duration > audio_clip.duration:
        audio_clip = audio_loop(audio_clip, duration=clip.duration)
    else:
        audio_clip = audio_clip.subclip(0, clip.duration)

    clip = clip.set_audio(audio_clip)
    return clip


def create_text_clip(text, duration=1.0):
    text_clip = TextClip(
        text,
        fontsize=50,
        color="white",
        size=(VIDEO_WIDTH, VIDEO_HEIGHT),
    )
    text_clip = text_clip.set_position("center")
    text_clip = text_clip.set_duration(duration)

    return text_clip


def create_canvas_with_image(image_paths, canvas_width=1080, canvas_height=1920):
    canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))

    for index, path in enumerate(image_paths):
        img = Image.open(path)

        if img.mode != "RGBA":
            img = img.convert("RGBA")

        x = (canvas_width - img.width) // 2
        if index == 0:
            y = int(0.05 * VIDEO_HEIGHT)
        else:
            y = int(0.55 * VIDEO_HEIGHT)

        canvas.paste(img, (x, y), img)

    canvas_np = np.array(canvas)
    return canvas_np


def generate_images_video(content_group):
    images, posts = get_images(content_group)
    if not images:
        return

    durations = [find_duration(img) for img in images]
    temp_video_path = f"temp_video_{int(datetime.datetime.now().timestamp())}.mp4"
    fps = 60

    background_clip = get_background(content_group.background)

    overlay_clips = []

    if content_group.start_text:
        text_clip = create_text_clip(content_group.start_text)
        overlay_clips.append(text_clip)

    media_per_screen = content_group.media_per_screen
    for i in range(0, len(images), media_per_screen):
        screen_images = images[i : i + media_per_screen]
        screen_duration = sum(durations[i : i + media_per_screen])

        screen_clips = []

        canvas_np = create_canvas_with_image(screen_images)

        img_clip = ImageClip(canvas_np).set_duration(screen_duration)

        screen_clips.append(img_clip)

        screen_clip = CompositeVideoClip(screen_clips)
        overlay_clips.append(screen_clip)

    if content_group.end_text:
        text_clip = create_text_clip(content_group.end_text)
        overlay_clips.append(text_clip)

    overlay_clip = concatenate_videoclips(overlay_clips, method="compose")

    if background_clip.duration < overlay_clip.duration:
        background_clip = background_clip.loop(duration=overlay_clip.duration)
    else:
        background_clip = background_clip.subclip(0, overlay_clip.duration)

    final_clip = CompositeVideoClip([background_clip, overlay_clip])
    final_clip = add_audio_to_clip(final_clip, audio_path)

    final_clip.write_videofile(temp_video_path, codec="libx264", fps=fps)

    metadata = {
        "length": final_clip.duration,
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
    for img in images:
        os.remove(img)

    return generated_video


def generate_text_video(content_group):
    pass


def generate_videos_video(content_group):
    pass
