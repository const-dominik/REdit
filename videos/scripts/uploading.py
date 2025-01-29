import os
import datetime
import requests
import time

from dotenv import load_dotenv

from static.libs.uploader.TiktokAutoUploader.tiktok_uploader import tiktok, cookies

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from videos.models import UploadedVideo

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def authenticate(type, version="v3"):
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "yt_credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build(type, version, credentials=creds)


def upload_file_to_drive(file_path, file_name):
    service = authenticate("drive")

    file_metadata = {"name": file_name}
    media = MediaFileUpload(file_path, resumable=True)
    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )
    file_id = file.get("id")

    service.permissions().create(
        fileId=file_id, body={"type": "anyone", "role": "reader"}
    ).execute()

    shareable_link = f"https://drive.google.com/uc?export=download&id={file_id}"
    return shareable_link


def upload_to_shorts(video):
    youtube = authenticate("youtube")
    try:
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": video.content_group.upload_description,
                    "description": "",
                    "tags": ["shorts", "shortvideo"],
                    "categoryId": "22",
                },
                "status": {"privacyStatus": "public"},
            },
            media_body=MediaFileUpload(video.video.path, chunksize=-1, resumable=True),
        )
        response = request.execute()

        UploadedVideo.objects.create(
            video=video, platform="Youtube", uploaded_video_id=response["id"]
        )
        print("Uploaded to shorts!")
    except Exception as e:
        print(f"An error occurred: {e}")


def upload_to_reels(video):
    drive_link = upload_file_to_drive(
        video.video.path, f"file_{int(datetime.datetime.now().timestamp())}.mp4"
    )

    # upload video
    upload_url = (
        f"https://graph.instagram.com/v22.0/{os.getenv("INSTA_ACCOUNT_ID")}/media"
    )
    publish_url = upload_url + "_publish"

    response = requests.post(
        upload_url,
        headers={"Content-Type": "application/json"},
        data={
            "media_type": "REELS",
            "video_url": drive_link,
            "access_token": os.getenv("INSTA_ACCESS_TOKEN"),
        },
    )

    data = response.json()
    if "id" not in data:
        print(data)
        print("Failed to upload to reels.")
        return

    id = response.json()["id"]

    # publish!
    def publish(id):
        response = requests.post(
            publish_url,
            headers={"Content-Type": "application/json"},
            data={
                "creation_id": id,
                "access_token": os.getenv("INSTA_ACCESS_TOKEN"),
            },
        )

        data = response.json()
        if "id" in data:
            return data["id"]

        if "error" in data and data["error"]["message"] == "Media ID is not available":
            print("Media not ready yet, retrying in 10s.")
            time.sleep(10)
            publish(id)

    reel_id = publish(id)

    UploadedVideo.objects.create(
        video=video, platform="Instagram", uploaded_video_id=reel_id
    )
    print("Uploaded to reels!")


def upload_to_tiktok(video):
    user = "REditMemer"
    tiktok.login(user)
    response = tiktok.upload_video(
        user, video.video.path, video.content_group.upload_description
    )

    if "single_post_resp_list" in response:
        resp = response["single_post_resp_list"]
        if "item_id" in resp:
            UploadedVideo.objects.create(
                video=video, platform="TikTok", uploaded_video_id=resp["item_id"]
            )
            print("Uploaded to TikTok!")


def upload_to_social_media(video):
    upload_to_shorts(video)
    upload_to_reels(video)
    upload_to_tiktok(video)
