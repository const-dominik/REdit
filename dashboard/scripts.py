import numpy as np
import requests
import os

from dotenv import load_dotenv

from videos.scripts.uploading import authenticate

load_dotenv()


def yt_response_to_np(response):
    column_headers = response["columnHeaders"]
    rows = response["rows"]

    dtype = [
        (
            header["name"],
            (
                "U20"
                if header["dataType"] == "STRING"
                else "f8" if header["dataType"] == "FLOAT" else "i8"
            ),
        )
        for header in column_headers
    ]

    structured_array = np.array([tuple(row) for row in rows], dtype=dtype)

    return structured_array


def yt_response_to_dict(response, key="video"):
    column_headers = response["columnHeaders"]
    rows = response["rows"]

    res_dict = {}

    for row in rows:
        res_dict[row[0]] = {}
        for value, column in zip(row[1:], column_headers[1:]):
            res_dict[row[0]][column["name"]] = value

    return res_dict


def get_stats_analytics(start_date="2025-01-21", end_date="2026-01-31"):
    service = authenticate("youtubeAnalytics", "v2")

    try:
        response = (
            service.reports()
            .query(
                ids="channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics="views,comments,likes,dislikes,shares,subscribersGained,subscribersLost,estimatedMinutesWatched,averageViewPercentage,averageViewDuration",
                dimensions="day",
                sort="day",
            )
            .execute()
        )
        return yt_response_to_np(response)
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def get_shorts_analytics(shorts_ids, start_date="2025-01-01", end_date="2026-01-31"):
    service = authenticate("youtubeAnalytics", "v2")

    try:
        shorts_ids_str = ",".join(shorts_ids)
        response = (
            service.reports()
            .query(
                ids="channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics="views,likes,dislikes,shares,comments,estimatedMinutesWatched,averageViewDuration,averageViewPercentage",
                dimensions="video",
                filters=f"video=={shorts_ids_str}",
            )
            .execute()
        )
        return yt_response_to_dict(response)
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def reels_data_simplified(res):
    data = res["data"] if "data" in res else res

    simple_data = {}
    for metric in data:
        value_container = (
            metric["total_value"] if "total_value" in metric else metric["values"][0]
        )

        simple_data[metric["name"]] = value_container["value"]

    return simple_data


def get_reels_analytics():
    ACCESS_TOKEN = os.getenv("INSTA_ACCESS_TOKEN")
    INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv("INSTA_ACCOUNT_ID")
    url = f"https://graph.instagram.com/v22.0/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/insights"

    metrics = [
        "accounts_engaged",
        "comments",
        "follower_count",
        "likes",
        "reach",
        "shares",
        "total_interactions",
        "views",
    ]

    params = {
        "metric": ",".join(metrics),
        "period": "day",
        "since": "2025-01-01",
        "until": "2026-01-01",
        "metric_type": "total_value",
        "access_token": ACCESS_TOKEN,
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        return reels_data_simplified(data)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def get_media_objects():
    ACCESS_TOKEN = os.getenv("INSTA_ACCESS_TOKEN")
    INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv("INSTA_ACCOUNT_ID")
    url = f"https://graph.instagram.com/v22.0/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media"

    params = {
        "access_token": ACCESS_TOKEN,
        "fields": "id,media_type,timestamp",
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        return list(map(lambda x: x["id"], data.get("data", [])))
    else:
        return []


def get_media_insights(media_id):
    ACCESS_TOKEN = os.getenv("INSTA_ACCESS_TOKEN")
    url = f"https://graph.instagram.com/v22.0/{media_id}/insights"

    metrics = [
        "comments",
        "ig_reels_avg_watch_time",
        "ig_reels_video_view_total_time",
        "likes",
        "reach",
        "saved",
        "shares",
        "total_interactions",
    ]

    params = {
        "metric": ",".join(metrics),
        "period": "day",
        "access_token": ACCESS_TOKEN,
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        return reels_data_simplified(data.get("data", []))
    else:
        return []


def get_all_media_insights():
    ids = get_media_objects()

    data = {}
    for id in ids:
        insights = get_media_insights(id)
        if len(insights) > 0:
            data[id] = insights
            data[id]["views"] = (
                int(
                    data[id]["ig_reels_video_view_total_time"]
                    / data[id]["ig_reels_avg_watch_time"]
                )
                if data[id]["ig_reels_avg_watch_time"] != 0
                else 0
            )
            data[id]["ig_reels_video_view_total_time"] = int(
                data[id]["ig_reels_video_view_total_time"] / (1000 * 60)
            )  # ms -> min
            data[id]["ig_reels_avg_watch_time"] /= 1000  # ms -> s
    return data
