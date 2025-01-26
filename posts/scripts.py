from dotenv import load_dotenv
import praw
import os
import requests
from google import genai

from datetime import datetime

from django.core.files.base import ContentFile
from django.db import IntegrityError

from posts.models import Subreddit, Post

load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_ID"),
    client_secret=os.getenv("REDDIT_SECRET"),
    user_agent=os.getenv("REDDIT_AGENT"),
    refresh_token=os.getenv("REFRESH_TOKEN"),
)

gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
model_name = "gemini-2.0-flash-exp"


def transfer_text(title, text):
    prompt = f"""I'm gonna give you a reddit post and it's title. It's gonna be uploaded on social media. Your task is:
    If you think that the post should be considered NSFW or contain some strong content that might get me banned (for example, weird sex stories, disgusting things, +18 things), respond with a signle "NO". It's super important.
    Otherwise, if you think the post is OK for social media, make sure that:
    - unabbreviate abbreviations, so that when I put it through tts model, it's gonna be nice to listen to (from title and content) (example - AITAH - Am i the asshole, but censor it like described further in prompt, LPT - life pro tip, it's from reddit if you need context).
    - text is around 250 words at most - you should shorten it if it's longer than that - it's super important so make sure you take care of this. Text shouldn't lose any meaning on shortening it, don't leave any important facts out in order to shorten it.
    - lightly censor vulgar words (for example: asshole to A-hole, so that it's still understandable but there's no ugly words), but words like ass are fine.
    - if text has been edited (something like "EDIT:" in text) you should remove that edit, you might integrate info from it straight to content

    Once you're done, again make sure the text is correct length and didn't lose any meaning - max 250 words of content.
    End content with some engagement-engaging text (like, for example in Am I the asshole reddit, "Who do you think is the A-hole?")
    Respond in the same format i send you the post, and just that, no additions from you.

    [TITLE]: {title}
    [CONTENT]: {text}
    """
    response = gemini.models.generate_content(model=model_name, contents=prompt)
    return response.text.strip()


def fetch_posts(subreddit, time_filter, amount):
    posts = reddit.subreddit(subreddit.name).top(
        time_filter=time_filter, limit=int(amount)
    )
    for post in posts:
        if not post.over_18:
            posted_at_datetime = datetime.fromtimestamp(post.created_utc)

            my_post_data = {
                "subreddit": subreddit,
                "title": post.title,
                "posted_at": posted_at_datetime,
                "author": post.author if post.author else "deleted",
                "post_id": post.id,
            }

            if "text" in subreddit.types and post.selftext:
                changed_text = transfer_text(post.title, post.selftext)
                if changed_text.strip() != "NO":
                    lines = changed_text.strip().split("\n")

                    title = lines[0].replace("[TITLE]:", "").strip()
                    content = lines[1].replace("[CONTENT]:", "").strip()

                    if len(lines) > 2:
                        for line in lines[2:]:
                            content += line

                    my_post_data["title"] = title
                    my_post_data["content"] = content

            if "img" in subreddit.types:
                if post.url.endswith(("jpg", "jpeg", "png")):
                    image_content = download_image(post.url)

                    if image_content:
                        image_file = ContentFile(
                            image_content, name=os.path.basename(post.url)
                        )
                        my_post_data["image"] = image_file

            if "vid" in subreddit.types and "." not in post.url[-5:]:
                if hasattr(post, "media") and post.media is not None:
                    video_url = post.media["reddit_video"]["fallback_url"]
                    video_url = video_url.split("?")[0]

                    if video_url is not None:
                        response = requests.get(video_url, stream=True)
                        if response.status_code == 200:
                            file_name = f"{post.id}.mp4"

                            my_post_data["video"] = ContentFile(
                                response.content, name=file_name
                            )
            try:
                if (
                    "content" in my_post_data
                    or "image" in my_post_data
                    or "video" in my_post_data
                ):
                    Post.objects.create(**my_post_data)
            except IntegrityError:
                print(f"Post with id '{post.id}' already exists, skipping.")
                continue


def download_image(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content

    except requests.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return None
