import os
import random

from moviepy.editor import ImageSequenceClip, AudioFileClip
from django.core.files import File
from django.utils import timezone
from PIL import Image
from io import BytesIO
from django.conf import settings

from posts.models import Post
from videos.models import GeneratedVideo

audio_path = os.path.join(settings.MEDIA_ROOT, "audio\\meme\\audio.mp3")


def resize_image(image_path, target_size):
    img = Image.open(image_path)
    img_resized = img.resize(target_size, Image.Resampling.LANCZOS)

    img_byte_arr = BytesIO()
    img_resized.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)
    return img_byte_arr


def get_images(content_group):
    posts = Post.objects.filter(
        subreddit__in=content_group.subreddits.all(), image__isnull=False
    )

    random_posts = random.sample(list(posts), 5)

    image_paths = [
        post.image.path for post in list(filter(lambda x: x.image, random_posts))
    ]

    target_size = Image.open(image_paths[0]).size
    resized_images = []

    for image_path in image_paths:
        resized_image = resize_image(image_path, target_size)
        resized_images.append(resized_image)

    temp_resized_image_paths = []

    for i, resized_img in enumerate(resized_images):
        temp_image_path = f"temp_image_{i}.png"
        with open(temp_image_path, "wb") as temp_image_file:
            temp_image_file.write(resized_img.getvalue())
        temp_resized_image_paths.append(temp_image_path)

    return temp_resized_image_paths


def generate_video(content_group):
    images = get_images(content_group)

    temp_video_path = "temp_video.mp4"

    image_clip = ImageSequenceClip(images, fps=1 / 5)

    audio_clip = AudioFileClip(audio_path)

    clip = image_clip.set_audio(audio_clip)

    clip.write_videofile(temp_video_path, codec="libx264")

    with open(temp_video_path, "rb") as video_file:
        video_content = File(video_file)
        generated_video = GeneratedVideo(
            video=video_content,
            length=clip.duration,
            content_group=content_group,
            created_at=timezone.now(),
        )
        generated_video.save()

    os.remove(temp_video_path)

    return generated_video
