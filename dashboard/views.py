import numpy as np
from numpy.lib import recfunctions as rfn

from django.views.generic import TemplateView
from dashboard.scripts import (
    get_stats_analytics,
    get_shorts_analytics,
    get_reels_analytics,
    get_all_media_insights,
)

from videos.models import UploadedVideo


def parse_audio_type(audio_path):
    _, audio = audio_path.split("audios\\")
    song_type, song = audio.split("\\")
    song_title, _ = song.split(".")

    return song_type, song_title


def round_float(num):
    return float("{:.2f}".format(num))


def get_detailed_data(data, videos):
    available_videos_ids = data.keys()
    for uploaded_video in videos:
        video_id = uploaded_video.uploaded_video_id
        video_data = uploaded_video.video.meta_data

        if video_id in available_videos_ids:
            entry = data[video_id]
            if "audio_used" in video_data:
                song_type, song_title = parse_audio_type(video_data["audio_used"])
                entry["song_type"] = song_type
                entry["song_title"] = song_title
            else:
                entry["song_type"] = "N/A"
                entry["song_title"] = "N/A"

            entry["video_type"] = video_data["video_type"]
            entry["content_group_name"] = uploaded_video.video.content_group.name
            entry["video_length"] = round_float(video_data["length"])
            entry["background"] = video_data["background"]
            entry["used_start_text"] = int(bool(video_data["start_text"]))
            entry["used_end_text"] = int(bool(video_data["end_text"]))
            entry["media_per_screen"] = video_data["media_per_screen"]
            entry["media_qty"] = video_data["media_qty"]
            entry["uploaded_day"] = uploaded_video.video.created_at.strftime("%Y-%m-%d")

    return data


class Dashboard(TemplateView):
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_name"] = "dashboard"

        # fetch data for yt shorts
        context["yt_shorts"] = get_stats_analytics()

        videos = UploadedVideo.objects.filter(platform="Youtube")
        video_ids = list(videos.values_list("uploaded_video_id", flat=True))

        shorts_data = get_shorts_analytics(list(video_ids))
        detailed_data = get_detailed_data(shorts_data, videos)
        context["detailed_yt_shorts"] = detailed_data

        # reels
        context["reels"] = get_reels_analytics()
        insights = get_all_media_insights()

        videos = UploadedVideo.objects.filter(platform="Instagram")
        video_ids = list(videos.values_list("uploaded_video_id", flat=True))

        insights_for_reels_in_db = {
            field: insights[field] for field in insights if field in video_ids
        }

        context["detailed_reels"] = get_detailed_data(insights_for_reels_in_db, videos)
        return context
