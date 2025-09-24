import random
import pytesseract
import os
from dotenv import load_dotenv

from django.conf import settings

from moviepy import (
    AudioFileClip,
    VideoFileClip,
    TextClip,
    afx,
)
from PIL import Image
from apps.posts.models import Post
from google import genai

from apps.videos.models import GeneratedVideo

load_dotenv()

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
)

audios_path = os.path.join(settings.STATIC_ROOT, "video_assets\\audios\\")
minecraft_path = os.path.join(
    settings.STATIC_ROOT, "video_assets\\backgrounds\\minecraft"
)
subway_path = os.path.join(settings.STATIC_ROOT, "video_assets\\backgrounds\\subway")
chill_path = os.path.join(settings.STATIC_ROOT, "video_assets\\backgrounds\\chill")
font_path = os.path.join(settings.STATIC_ROOT, "video_assets\\font.otf")

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

chill_files = [
    f"{chill_path}\\{f}"
    for f in os.listdir(chill_path)
    if os.path.isfile(os.path.join(chill_path, f))
]

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920


def transfer_text(title, text):
    gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    model_name = "gemini-2.0-flash-exp"
    prompt = f"""I'm gonna give you a reddit post and it's title. It's gonna be uploaded on social media. Your task is:
    If you think that the post should be considered NSFW or contain some strong content that might get me banned (for example, weird sex stories, disgusting things, +18 things), respond with a signle "NO". It's super important.
    Otherwise, if you think the post is OK for social media, make sure that:
    - unabbreviate abbreviations, so that when I put it through tts model, it's gonna be nice to listen to (from title and content) (example - AITAH - Am i the asshole, but censor it like described further in prompt, LPT - life pro tip, it's from reddit if you need context).
    - text is around 250 words at most - you should shorten it if it's longer than that - it's super important so make sure you take care of this. Text shouldn't lose any meaning on shortening it, don't leave any important facts out in order to shorten it.
    - lightly censor vulgar words (for example: asshole to A-hole, so that it's still understandable but there's no ugly words), but words like ass are fine.
    - if text has been edited (something like "EDIT:" in text) you should remove that edit, you might integrate info from it straight to content

    Once you're done, again make sure the text is correct length and didn't lose any meaning - max 250 words of content.
    End content with some engagement-engaging text (like, for example in Am I the asshole reddit, "Who do you think is the A-hole?")
    Respond in the same format I send you the post (so the [TITLE]: in given section, a newline and a [CONTENT]:), and just that, no additions from you.

    [TITLE]: {title}
    [CONTENT]: {text}
    """
    response = gemini.models.generate_content(model=model_name, contents=prompt)
    return response.text.strip()


def get_media(content_group, media_type):
    used_post_ids = (
        GeneratedVideo.objects.exclude(used_media__isnull=True)
        .values_list("used_media__post_id", flat=True)
        .distinct()
    )

    unused_posts = Post.objects.filter(
        subreddit__in=content_group.subreddits.all()
    ).exclude(post_id__in=used_post_ids)

    if media_type == "img":
        posts = unused_posts.filter(image__isnull=False)
        media_field = "image"
    elif media_type == "vid":
        posts = unused_posts.filter(video__isnull=False).exclude(video="")
        media_field = "video"
    elif media_type == "txt":
        posts = unused_posts.filter(
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
    else:
        post = random_posts[0]
        changed_text = transfer_text(post.title, post.content)
        if changed_text.strip() != "NO":
            lines = changed_text.strip().split("\n")

            title = lines[0].replace("[TITLE]:", "").strip()
            content = lines[1].replace("[CONTENT]:", "").strip()

            if len(lines) > 2:
                for line in lines[2:]:
                    content += line

            post.title = title
            post.content = content
            post.save()

            # whatever content group says, we always do 1 reading content per video
            return [], post
        else:
            post.delete()
            return get_media(content_group, media_type)


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
    elif background_type == "chill":
        video = random.choice(chill_files)
        return VideoFileClip(video)
    return get_background("minecraft" if random.random() < 0.5 else "subway")


def find_duration(image_path):
    words = find_words_in_image(image_path) - 10
    duration = 5

    if words > 0:
        duration += words / 6

    return duration


def resize_media(
    media_path,
    target_size=(VIDEO_WIDTH, VIDEO_HEIGHT),
    media_type="img",
    mode="halfscreen",
):
    if media_type == "img":
        img = Image.open(media_path)

        target_width, target_height = target_size
        height_scalar = 0.8 if mode == "fullscreen" else 0.4
        max_width, max_height = target_width * 0.9, target_height * height_scalar

        ratio = min(max_width / img.width, max_height / img.height)
        new_width = int(img.width * ratio)
        new_height = int(img.height * ratio)

        upscale = ratio > 1.0
        resample = Image.Resampling.BICUBIC if upscale else Image.Resampling.LANCZOS

        img = img.resize((new_width, new_height), resample)

        return img
    elif media_type == "vid":
        video_clip = VideoFileClip(media_path)

        aspect_ratio = video_clip.size[0] / video_clip.size[1]
        if aspect_ratio > (target_size[0] / target_size[1]):
            new_width = int(target_size[0] * 0.9)
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = int(target_size[1] * 0.45)
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


def get_audio(group):
    song_type = group.song_type if group.song_type else "upbeat-popular"
    song_title = group.song_title if group.song_title else "random"

    song_dir = os.path.join(audios_path, song_type)
    if song_dir:
        if song_title != "random":
            return os.path.join(song_dir, song_title)
        else:
            songs = os.listdir(song_dir)
            return os.path.join(song_dir, random.choice(songs))
