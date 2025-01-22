import os
import random
import datetime
import pytesseract

from moviepy.editor import (
    ImageSequenceClip,
    ImageClip,
    AudioFileClip,
    TextClip,
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

audio_path = os.path.join(settings.MEDIA_ROOT, "audio\\meme\\audio2.mp3")
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


def find_duration(image_path):
    words = find_words_in_image(image_path) - 10
    duration = 5

    if words > 0:
        duration += words / 6

    return duration


def resize_image(image_path):
    target_size = (720, 1280)
    img = Image.open(image_path)

    target_width, target_height = target_size

    img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)

    background = Image.new("RGB", (target_width, target_height), (0, 0, 0))

    x = (target_width - img.width) // 2
    y = (target_height - img.height) // 2

    background.paste(img, (x, y))

    img_byte_arr = BytesIO()
    background.save(img_byte_arr, format="PNG", quality=100)
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

    return temp_resized_image_paths


def generate_images_video(content_group):
    images = get_images(content_group)
    durations = [find_duration(img) for img in images]

    if not images:
        return

    temp_video_path = f"temp_video_{int(datetime.datetime.now().timestamp())}.mp4"

    clips = []
    fps = 30

    if content_group.start_text:
        start_text_clip = TextClip(
            content_group.start_text,
            fontsize=50,
            color="white",
            size=(720, 1280),
        )
        start_text_clip = start_text_clip.set_position("center")
        start_text_clip = start_text_clip.set_duration(1.0)
        clips.append(start_text_clip)

    for img, duration in zip(images, durations):
        img_clip = ImageClip(img).set_duration(duration)
        clips.append(img_clip)

    if content_group.end_text:
        end_text_clip = TextClip(
            content_group.end_text,
            fontsize=50,
            color="white",
            size=(720, 1280),
        )
        end_text_clip = end_text_clip.set_position("center")
        end_text_clip = end_text_clip.set_duration(1.0)
        clips.append(end_text_clip)

    final_clip = concatenate_videoclips(clips)

    audio_clip = AudioFileClip(audio_path)

    if final_clip.duration > audio_clip.duration:
        audio_clip = audio_loop(audio_clip, duration=final_clip.duration)
    else:
        audio_clip = audio_clip.subclip(0, final_clip.duration)

    final_clip = final_clip.set_audio(audio_clip)

    final_clip.write_videofile(temp_video_path, codec="libx264", fps=fps)

    with open(temp_video_path, "rb") as video_file:
        video_content = File(video_file)
        generated_video = GeneratedVideo.objects.create(
            video=video_content,
            length=final_clip.duration,
            content_group=content_group,
            created_at=timezone.now(),
        )

    os.remove(temp_video_path)

    for img in images:
        os.remove(img)

    return generated_video


def generate_text_video(content_group):
    pass


def generate_videos_video(content_group):
    pass
