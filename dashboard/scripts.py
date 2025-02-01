import numpy as np

from googleapiclient.discovery import build

from videos.scripts.uploading import authenticate


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
