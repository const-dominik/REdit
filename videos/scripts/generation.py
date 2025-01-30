import os
import random
import datetime
import numpy as np

from moviepy import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    concatenate_videoclips,
)

from moviepy.video.fx import Loop

from moviepy.audio.AudioClip import CompositeAudioClip

from django.core.files import File
from django.utils import timezone
from PIL import Image

from videos.models import GeneratedVideo
from videos.scripts.tts import get_transcribed_tts
from videos.scripts.uploading import upload_to_social_media
from videos.scripts.utils import (
    find_duration,
    get_background,
    resize_media,
    add_audio_to_clip,
    get_media,
    audio_path,
    create_text_clip,
)


def generate_video(content_group):
    if content_group.type == "img":
        generated_video = generate_media_video(content_group, media_type="img")
    elif content_group.type == "vid":
        generated_video = generate_media_video(content_group, media_type="vid")
    elif content_group.type == "text":
        generated_video = generate_text_video(content_group)
    upload_to_social_media(generated_video)


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
                y = int(0.5 * canvas_height)

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
                    y = int(0.5 * canvas_height)

            video_clips_with_positions.append(resized_clip.with_position((x, y)))

        composite_clip = CompositeVideoClip([canvas_clip] + video_clips_with_positions)

        return composite_clip
    else:
        raise ValueError("Invalid media type. Use 'img' or 'vid'.")


def generate_media_video(content_group, media_type="img"):
    media_result = get_media(content_group, media_type)
    if not media_result:
        print("No media found for the content group.")
        return

    media_paths, posts = media_result

    temp_video_path = f"temp_video_{int(datetime.datetime.now().timestamp())}.mp4"
    fps = 60

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

    return generated_video


def generate_text_video(content_group):
    media_result = get_media(content_group, "txt")
    if not media_result:
        print("No text media found for the content group.")
        return

    _, posts = media_result

    for post in posts:
        title_audio_path, _ = get_transcribed_tts(post.title, 0.9)
        content_audio_path, timestamps = get_transcribed_tts(post.content, 0.9)

        background_clip = get_background(content_group.background)

        text_clips = []

        title_audio_clip = AudioFileClip(title_audio_path)
        title_duration = title_audio_clip.duration
        title_clip = create_text_clip(
            post.title, is_title=True, duration=title_duration, font_size=75
        )
        title_clip = title_clip.with_audio(title_audio_clip)
        text_clips.append(title_clip)

        for word, start_time, end_time in timestamps:
            word_clip = create_text_clip(
                word, duration=end_time - start_time, font_size=100
            )
            word_clip = word_clip.with_start(start_time + title_duration)
            text_clips.append(word_clip)

        final_text_clip = CompositeVideoClip(text_clips)

        content_audio_clip = AudioFileClip(content_audio_path).with_start(
            title_duration
        )

        final_audio_clip = CompositeAudioClip([title_audio_clip, content_audio_clip])

        final_text_clip = final_text_clip.with_duration(final_audio_clip.duration)

        if background_clip.duration < final_text_clip.duration:
            background_clip = background_clip.with_effects(
                [Loop(duration=final_text_clip.duration)]
            )
        else:
            background_clip = background_clip.subclipped(0, final_text_clip.duration)

        final_clip = CompositeVideoClip([background_clip, final_text_clip]).with_audio(
            final_audio_clip
        )

        temp_video_path = (
            f"temp_text_video_{int(datetime.datetime.now().timestamp())}.mp4"
        )
        final_clip.write_videofile(temp_video_path, codec="libx264", fps=60)

        metadata = {
            "length": float(final_clip.duration),
            "background": content_group.background,
            "media_per_screen": content_group.media_per_screen,
            "media_qty": len(posts),
            "video_type": content_group.type,
            "start_text": content_group.start_text,
            "end_text": content_group.end_text,
            "title": post.title,
            "content": post.content,
        }

        with open(temp_video_path, "rb") as video_file:
            video_content = File(video_file)
            generated_video = GeneratedVideo.objects.create(
                video=video_content,
                content_group=content_group,
                created_at=timezone.now(),
                meta_data=metadata,
            )
            generated_video.used_media.set([post])

        os.remove(temp_video_path)
        os.remove(title_audio_path)
        os.remove(content_audio_path)

        return generated_video
