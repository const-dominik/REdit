from moviepy.editor import ImageSequenceClip
from django.core.files import File
from django.utils import timezone
from PIL import Image
import os
from io import BytesIO

from posts.models import Post
from videos.models import GeneratedVideo


def resize_image(image_path, target_size):
    img = Image.open(image_path)
    img_resized = img.resize(target_size, Image.Resampling.LANCZOS)

    img_byte_arr = BytesIO()
    img_resized.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)
    return img_byte_arr


def generate_video(content_group):
    posts = Post.objects.filter(
        subreddit__in=content_group.subreddits.all(), image__isnull=False
    )[:5]

    image_paths = [post.image.path for post in posts]

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

    clip = ImageSequenceClip(temp_resized_image_paths, fps=1 / 5)
    temp_video_path = "temp_video.mp4"
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

    for temp_image_path in temp_resized_image_paths:
        os.remove(temp_image_path)
    os.remove(temp_video_path)

    return generated_video
