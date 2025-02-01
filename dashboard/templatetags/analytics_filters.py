from django import template
from statistics import mean
from collections import defaultdict
from datetime import datetime

import numpy as np


register = template.Library()


@register.filter
def sum_by_field(data, field):
    """Sum a field in the NumPy structured array."""
    try:
        return int(np.sum(data[field]))
    except Exception:
        return 0


@register.filter
def pluck_field(data, field):
    """Extract a field from the NumPy structured array as a list."""
    try:
        return list(data[field])
    except Exception:
        return []


@register.filter
def net_subscribers(data, fields):
    """Calculate net subscribers gained/lost."""
    try:
        field1, field2 = fields.split(",")
        gained = int(np.sum(data[field1]))
        lost = int(np.sum(data[field2]))
        return gained - lost
    except Exception:
        return 0


@register.filter
def total_engagement(data, fields):
    """Calculate total engagement by summing specified fields (likes, comments, shares) over time."""
    try:
        field_list = fields.split(",")
        engagement_data = []

        field_indices = {
            "likes": 3,
            "comments": 2,
            "shares": 5,
        }

        for item in data:
            total = 0
            for field in field_list:
                if field in field_indices:
                    index = field_indices[field]
                    total += max(int(item[index]), 0)

            engagement_data.append(total)

        return engagement_data
    except Exception as e:
        print(f"Error in total_engagement filter: {e}")
        return []


@register.filter
def average(data, field):
    "Caluclate average"
    try:
        return float("{:.2f}".format(mean(data[field])))
    except Exception:
        return 0


def calculate_avg_views(detailed_yt_shorts, category_key):
    category_views = defaultdict(lambda: {"total_views": 0, "count": 0})

    for short_id, data in detailed_yt_shorts.items():
        category = data.get(category_key, "Unknown")
        views = data.get("views", 0)
        category_views[category]["total_views"] += views
        category_views[category]["count"] += 1

    avg_views = {
        category: stats["total_views"] / stats["count"]
        for category, stats in category_views.items()
    }

    return {"labels": list(avg_views.keys()), "values": list(avg_views.values())}


@register.simple_tag
def get_views_distribution_by_content_group(detailed_yt_shorts):
    return calculate_avg_views(detailed_yt_shorts, "content_group_name")


@register.simple_tag
def get_engagement_rate_by_content_group(detailed_yt_shorts):
    content_group_engagement = defaultdict(
        lambda: {"likes": 0, "comments": 0, "shares": 0, "count": 0}
    )

    for short_id, data in detailed_yt_shorts.items():
        content_group = data.get("content_group_name", "Unknown")
        likes = data.get("likes", 0)
        comments = data.get("comments", 0)
        shares = data.get("shares", 0)

        content_group_engagement[content_group]["likes"] += likes
        content_group_engagement[content_group]["comments"] += comments
        content_group_engagement[content_group]["shares"] += shares
        content_group_engagement[content_group]["count"] += 1

    avg_engagement = {
        group: {
            "likes": engagement["likes"] / engagement["count"],
            "comments": engagement["comments"] / engagement["count"],
            "shares": engagement["shares"] / engagement["count"],
        }
        for group, engagement in content_group_engagement.items()
    }

    labels = list(avg_engagement.keys())
    likes = [engagement["likes"] for engagement in avg_engagement.values()]
    comments = [engagement["comments"] for engagement in avg_engagement.values()]
    shares = [engagement["shares"] for engagement in avg_engagement.values()]

    return {
        "labels": labels,
        "datasets": [
            {
                "label": "Likes",
                "data": likes,
                "backgroundColor": "rgba(255, 99, 132, 0.6)",
            },
            {
                "label": "Comments",
                "data": comments,
                "backgroundColor": "rgba(54, 162, 235, 0.6)",
            },
            {
                "label": "Shares",
                "data": shares,
                "backgroundColor": "rgba(75, 192, 192, 0.6)",
            },
        ],
    }


@register.simple_tag
def get_avg_views_per_video_type(detailed_yt_shorts):
    return calculate_avg_views(detailed_yt_shorts, "video_type")


@register.simple_tag
def get_avg_views_per_song_type(detailed_yt_shorts):
    return calculate_avg_views(detailed_yt_shorts, "song_type")


@register.simple_tag
def get_avg_views_per_song_title(detailed_yt_shorts):
    return calculate_avg_views(detailed_yt_shorts, "song_title")


@register.simple_tag
def get_avg_views_per_background(detailed_yt_shorts):
    return calculate_avg_views(detailed_yt_shorts, "background")


@register.simple_tag
def get_avg_views_per_media_per_screen(detailed_yt_shorts):
    return calculate_avg_views(detailed_yt_shorts, "media_per_screen")


@register.simple_tag
def get_avg_views_per_media_qty(detailed_yt_shorts):
    return calculate_avg_views(detailed_yt_shorts, "media_qty")


@register.simple_tag
def get_avg_views_per_text_usage(detailed_yt_shorts, text_type):
    text_usage_views = defaultdict(lambda: {"total_views": 0, "count": 0})

    for short_id, data in detailed_yt_shorts.items():
        used_text = data.get(f"used_{text_type}_text", False)
        views = data.get("views", 0)
        text_usage_views[used_text]["total_views"] += views
        text_usage_views[used_text]["count"] += 1

    avg_views = {
        "Used" if used else "Not Used": stats["total_views"] / stats["count"]
        for used, stats in text_usage_views.items()
    }

    return {"labels": list(avg_views.keys()), "values": list(avg_views.values())}


def calculate_avg_engagement(detailed_yt_shorts, category_key):
    category_engagement = defaultdict(
        lambda: {"likes": 0, "comments": 0, "shares": 0, "count": 0}
    )

    for short_id, data in detailed_yt_shorts.items():
        category = data.get(category_key, "Unknown")
        likes = data.get("likes", 0)
        comments = data.get("comments", 0)
        shares = data.get("shares", 0)

        category_engagement[category]["likes"] += likes
        category_engagement[category]["comments"] += comments
        category_engagement[category]["shares"] += shares
        category_engagement[category]["count"] += 1

    avg_engagement = {
        category: {
            "likes": engagement["likes"] / engagement["count"],
            "comments": engagement["comments"] / engagement["count"],
            "shares": engagement["shares"] / engagement["count"],
        }
        for category, engagement in category_engagement.items()
    }

    labels = list(avg_engagement.keys())
    likes = [engagement["likes"] for engagement in avg_engagement.values()]
    comments = [engagement["comments"] for engagement in avg_engagement.values()]
    shares = [engagement["shares"] for engagement in avg_engagement.values()]

    return {
        "labels": labels,
        "datasets": [
            {
                "label": "Likes",
                "data": likes,
                "backgroundColor": "rgba(255, 99, 132, 0.6)",
            },
            {
                "label": "Comments",
                "data": comments,
                "backgroundColor": "rgba(54, 162, 235, 0.6)",
            },
            {
                "label": "Shares",
                "data": shares,
                "backgroundColor": "rgba(75, 192, 192, 0.6)",
            },
        ],
    }


@register.simple_tag
def get_avg_engagement_per_video_type(detailed_yt_shorts):
    return calculate_avg_engagement(detailed_yt_shorts, "video_type")


@register.simple_tag
def get_avg_engagement_per_song_type(detailed_yt_shorts):
    return calculate_avg_engagement(detailed_yt_shorts, "song_type")


@register.simple_tag
def get_avg_engagement_per_song_title(detailed_yt_shorts):
    return calculate_avg_engagement(detailed_yt_shorts, "song_title")


@register.simple_tag
def get_avg_engagement_per_background(detailed_yt_shorts):
    return calculate_avg_engagement(detailed_yt_shorts, "background")


@register.simple_tag
def get_avg_engagement_per_media_per_screen(detailed_yt_shorts):
    return calculate_avg_engagement(detailed_yt_shorts, "media_per_screen")


@register.simple_tag
def get_avg_engagement_per_media_qty(detailed_yt_shorts):
    return calculate_avg_engagement(detailed_yt_shorts, "media_qty")


@register.simple_tag
def get_avg_engagement_per_start_text(detailed_yt_shorts):
    return calculate_avg_engagement(detailed_yt_shorts, "used_start_text")


@register.simple_tag
def get_avg_engagement_per_end_text(detailed_yt_shorts):
    return calculate_avg_engagement(detailed_yt_shorts, "used_end_text")


@register.simple_tag
def get_video_length_vs_view_metrics(detailed_yt_shorts):
    video_lengths = []
    avg_view_percentages = []
    avg_view_durations = []

    for short_id, data in detailed_yt_shorts.items():
        video_length = data.get("video_length", 0)
        avg_view_percentage = data.get("averageViewPercentage", 0)
        avg_view_duration = data.get("averageViewDuration", 0)

        video_lengths.append(video_length)
        avg_view_percentages.append(avg_view_percentage)
        avg_view_durations.append(avg_view_duration)

    return {
        "video_lengths": video_lengths,
        "avg_view_percentages": avg_view_percentages,
        "avg_view_durations": avg_view_durations,
    }


def calculate_avg_watch_percentage(detailed_yt_shorts, category_key):
    category_watch_percentage = defaultdict(
        lambda: {"total_watch_percentage": 0, "count": 0}
    )

    for short_id, data in detailed_yt_shorts.items():
        category = data.get(category_key, "Unknown")
        watch_percentage = data.get("averageViewPercentage", 0)

        category_watch_percentage[category][
            "total_watch_percentage"
        ] += watch_percentage
        category_watch_percentage[category]["count"] += 1

    avg_watch_percentage = {
        category: stats["total_watch_percentage"] / stats["count"]
        for category, stats in category_watch_percentage.items()
    }

    return {
        "labels": list(avg_watch_percentage.keys()),
        "values": list(avg_watch_percentage.values()),
    }


@register.simple_tag
def get_avg_watch_percentage_per_content_group(detailed_yt_shorts):
    return calculate_avg_watch_percentage(detailed_yt_shorts, "content_group_name")


@register.simple_tag
def get_avg_watch_percentage_per_video_type(detailed_yt_shorts):
    return calculate_avg_watch_percentage(detailed_yt_shorts, "video_type")


@register.simple_tag
def get_avg_watch_percentage_per_song_type(detailed_yt_shorts):
    return calculate_avg_watch_percentage(detailed_yt_shorts, "song_type")


@register.simple_tag
def get_avg_watch_percentage_per_song_title(detailed_yt_shorts):
    return calculate_avg_watch_percentage(detailed_yt_shorts, "song_title")


@register.simple_tag
def get_avg_watch_percentage_per_background(detailed_yt_shorts):
    return calculate_avg_watch_percentage(detailed_yt_shorts, "background")


@register.simple_tag
def get_avg_watch_percentage_per_media_per_screen(detailed_yt_shorts):
    return calculate_avg_watch_percentage(detailed_yt_shorts, "media_per_screen")


@register.simple_tag
def get_avg_watch_percentage_per_media_qty(detailed_yt_shorts):
    return calculate_avg_watch_percentage(detailed_yt_shorts, "media_qty")


@register.simple_tag
def get_avg_watch_percentage_per_start_text(detailed_yt_shorts):
    return calculate_avg_watch_percentage(detailed_yt_shorts, "used_start_text")


@register.simple_tag
def get_avg_watch_percentage_per_end_text(detailed_yt_shorts):
    return calculate_avg_watch_percentage(detailed_yt_shorts, "used_end_text")


@register.simple_tag
def get_avg_views_per_shorts_posted(detailed_yt_shorts):
    shorts_per_day = defaultdict(lambda: {"total_views": 0, "count": 0})

    for short_id, data in detailed_yt_shorts.items():
        uploaded_day = data.get("uploaded_day", "Unknown")
        views = data.get("views", 0)

        shorts_per_day[uploaded_day]["total_views"] += views
        shorts_per_day[uploaded_day]["count"] += 1

    avg_views_per_day = {
        day: stats["total_views"] / stats["count"]
        for day, stats in shorts_per_day.items()
    }

    shorts_count_views = defaultdict(lambda: {"total_views": 0, "count": 0})
    for day, avg_views in avg_views_per_day.items():
        num_shorts = shorts_per_day[day]["count"]
        shorts_count_views[num_shorts]["total_views"] += avg_views
        shorts_count_views[num_shorts]["count"] += 1

    avg_views_per_shorts_count = {
        num_shorts: stats["total_views"] / stats["count"]
        for num_shorts, stats in shorts_count_views.items()
    }

    sorted_avg_views = sorted(avg_views_per_shorts_count.items(), key=lambda x: x[0])

    return {
        "labels": [f"{item[0]} shorts" for item in sorted_avg_views],
        "values": [item[1] for item in sorted_avg_views],
    }


@register.simple_tag
def get_avg_views_per_day_of_week(detailed_yt_shorts):
    day_of_week_views = defaultdict(lambda: {"total_views": 0, "count": 0})

    for short_id, data in detailed_yt_shorts.items():
        uploaded_day = data.get("uploaded_day", "Unknown")
        views = data.get("views", 0)

        try:
            day = datetime.strptime(uploaded_day, "%Y-%m-%d").strftime("%A")
        except ValueError:
            day = "Unknown"

        day_of_week_views[day]["total_views"] += views
        day_of_week_views[day]["count"] += 1

    avg_views_per_day = {
        day: stats["total_views"] / stats["count"]
        for day, stats in day_of_week_views.items()
    }

    days_of_week = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    for day in days_of_week:
        if day not in avg_views_per_day:
            avg_views_per_day[day] = 0

    sorted_avg_views = {day: avg_views_per_day[day] for day in days_of_week}

    return {
        "labels": list(sorted_avg_views.keys()),
        "values": list(sorted_avg_views.values()),
    }
