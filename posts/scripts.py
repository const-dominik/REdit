from dotenv import load_dotenv
import praw
import os
import requests
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


def fetch_posts(subreddit, time_filter, amount):
    posts = reddit.subreddit(subreddit.name).top(
        time_filter=time_filter, limit=int(amount)
    )
    for post in posts:
        if not post.over_18:  # dont wanna get banned :(
            posted_at_datetime = datetime.fromtimestamp(post.created_utc)

            my_post_data = {
                "subreddit": subreddit,
                "title": post.title,
                "posted_at": posted_at_datetime,
                "author": post.author if post.author else "deleted",
                "post_id": post.id,
            }

            if "text" in subreddit.types and post.selftext:
                if len(post.selftext) <= 2000:
                    my_post_data["content"] = post.selftext
                else:
                    continue

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
                print(f"Post with title '{post.title}' already exists, skipping.")
                continue


def download_image(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content

    except requests.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return None


def get_video_link(url):
    headers = {"User-Agent": os.getenv("REDDIT_AGENT")}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()

        try:
            video_url = data[0]["data"]["children"][0]["data"]["secure_media"][
                "reddit_video"
            ]["fallback_url"]
            return video_url
        except (KeyError, IndexError, TypeError):
            return None
