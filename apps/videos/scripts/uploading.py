import os
import datetime
import requests
import time
import dropbox

from dotenv import load_dotenv

from static.libs.uploader.TiktokAutoUploader.tiktok_uploader import tiktok, cookies

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from apps.videos.models import UploadedVideo

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def get_dbx_instance():
    access_token = generate_dropbox_access_token()
    instance = dropbox.Dropbox(access_token)

    return instance


def authenticate(type, version="v3"):
    credentials = None
    if os.path.exists("token.json"):
        credentials = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "yt_credentials.json", SCOPES
            )
            credentials = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(credentials.to_json())
    return build(type, version, credentials=credentials)


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


def generate_dropbox_access_token():
    url = "https://api.dropbox.com/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "refresh_token",
        "refresh_token": os.getenv("DROPBOX_REFRESH_TOKEN"),
        "client_id": os.getenv("DROPBOX_APP_KEY"),
        "client_secret": os.getenv("DROPBOX_APP_SECRET"),
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        return response.json().get("access_token")

    raise Exception("Something went wrong with token generation.")


def upload_to_dropbox(video, filename):
    dbx = get_dbx_instance()

    try:
        with open(video.video.path, "rb") as file:
            dbx.files_upload(
                file.read(), filename, mode=dropbox.files.WriteMode("overwrite")
            )

        link = dbx.sharing_create_shared_link_with_settings(filename).url
        direct_link = link.replace(
            "www.dropbox.com", "dl.dropboxusercontent.com"
        ).replace("?dl=0", "")
        return direct_link

    except Exception as e:
        print("Filed to upload file to dropbox", e)


def remove_from_dropbox(filename):
    dbx = get_dbx_instance()
    dbx.files_delete_v2(filename)


def upload_to_reels(video):
    filename = f"/reels/file_{int(datetime.datetime.now().timestamp())}.mp4"
    dropbox_link = upload_to_dropbox(video, filename)

    if not dropbox_link:
        print("Dropbox upload failed, terminating reel upload.")
        return

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
            "video_url": dropbox_link,
            "access_token": os.getenv("INSTA_ACCESS_TOKEN"),
        },
    )

    data = response.json()
    if "id" not in data:
        print(data)
        print("Failed to upload to reels.")
        return

    id = response.json()["id"]

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
            return publish(id)
        elif "error" in data:
            print("Something went wrong:", data)

    reel_id = publish(id)

    UploadedVideo.objects.create(
        video=video, platform="Instagram", uploaded_video_id=reel_id
    )
    remove_from_dropbox(filename)
    print("Uploaded to reels!")


def extract_tags(title):
    parts = title.split("#")
    new_title = parts[0].strip()
    tags = list(map(lambda x: x.strip(), parts[1:]))

    return new_title, tags


def upload_to_tiktok(video):
    user = "REditMemer"
    tiktok.login(user)
    title, tags = extract_tags(video.content_group.upload_description)
    # TODO: make tags work

    response = tiktok.upload_video(user, video.video.path, title)

    if response is not False and "single_post_resp_list" in response:
        resp = response["single_post_resp_list"][0]
        if "item_id" in resp:
            UploadedVideo.objects.create(
                video=video, platform="TikTok", uploaded_video_id=resp["item_id"]
            )
            print("Uploaded to TikTok!")


def upload_to_social_media(video):
    upload_to_shorts(video)
    upload_to_reels(video)
    upload_to_tiktok(video)
