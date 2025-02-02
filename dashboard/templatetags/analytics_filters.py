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


@register.filter
def average_watch_time(data):
    count = 0
    watch_percentage = 0

    for id, vid in data.items():
        count += 1
        watch_percentage += vid["ig_reels_avg_watch_time"] / vid["video_length"]

    return float("{:.2f}".format(watch_percentage * 100 / count))


@register.filter
def watch_in_total(data):
    total = 0
    for id, vid in data.items():
        total += vid["ig_reels_video_view_total_time"]

    return int(total)


# mess from now on


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


# Reusable function to calculate average views per category
def calculate_avg_views(instagram_data, category_key):
    category_views = defaultdict(lambda: {"total_views": 0, "count": 0})

    for reel_id, data in instagram_data.items():
        category = data.get(category_key, "Unknown")
        views = data.get("views", 0)

        # Sum views and count the number of reels per category
        category_views[category]["total_views"] += views
        category_views[category]["count"] += 1

    # Calculate average views per category
    avg_views = {
        category: stats["total_views"] / stats["count"]
        for category, stats in category_views.items()
    }

    return {"labels": list(avg_views.keys()), "values": list(avg_views.values())}


# Template tags using the reusable function
@register.simple_tag
def get_instagram_avg_views_per_content_group(instagram_data):
    return calculate_avg_views(instagram_data, "content_group_name")


@register.simple_tag
def get_instagram_avg_views_per_video_type(instagram_data):
    return calculate_avg_views(instagram_data, "video_type")


@register.simple_tag
def get_instagram_avg_views_per_song_type(instagram_data):
    return calculate_avg_views(instagram_data, "song_type")


@register.simple_tag
def get_instagram_avg_views_per_song_title(instagram_data):
    return calculate_avg_views(instagram_data, "song_title")


@register.simple_tag
def get_instagram_avg_views_per_background(instagram_data):
    return calculate_avg_views(instagram_data, "background")


@register.simple_tag
def get_instagram_avg_views_per_media_per_screen(instagram_data):
    return calculate_avg_views(instagram_data, "media_per_screen")


@register.simple_tag
def get_instagram_avg_views_per_media_qty(instagram_data):
    return calculate_avg_views(instagram_data, "media_qty")


@register.simple_tag
def get_instagram_avg_views_per_start_text(instagram_data):
    return calculate_avg_views(instagram_data, "used_start_text")


@register.simple_tag
def get_instagram_avg_views_per_end_text(instagram_data):
    return calculate_avg_views(instagram_data, "used_end_text")


# Reusable function to calculate average engagement per category
def calculate_avg_engagement(instagram_data, category_key):
    category_engagement = defaultdict(
        lambda: {"likes": 0, "comments": 0, "shares": 0, "saved": 0, "count": 0}
    )

    for reel_id, data in instagram_data.items():
        category = data.get(category_key, "Unknown")
        likes = data.get("likes", 0)
        comments = data.get("comments", 0)
        shares = data.get("shares", 0)
        saved = data.get("saved", 0)

        # Sum engagement metrics and count the number of reels per category
        category_engagement[category]["likes"] += likes
        category_engagement[category]["comments"] += comments
        category_engagement[category]["shares"] += shares
        category_engagement[category]["saved"] += saved
        category_engagement[category]["count"] += 1

    # Calculate average engagement per category
    avg_engagement = {
        category: {
            "likes": engagement["likes"] / engagement["count"],
            "comments": engagement["comments"] / engagement["count"],
            "shares": engagement["shares"] / engagement["count"],
            "saved": engagement["saved"] / engagement["count"],
        }
        for category, engagement in category_engagement.items()
    }

    # Convert to a format suitable for Chart.js
    labels = list(avg_engagement.keys())
    likes = [engagement["likes"] for engagement in avg_engagement.values()]
    comments = [engagement["comments"] for engagement in avg_engagement.values()]
    shares = [engagement["shares"] for engagement in avg_engagement.values()]
    saved = [engagement["saved"] for engagement in avg_engagement.values()]

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
            {
                "label": "Saved",
                "data": saved,
                "backgroundColor": "rgba(153, 102, 255, 0.6)",
            },
        ],
    }


# Template tags using the reusable function
@register.simple_tag
def get_instagram_engagement_per_content_group(instagram_data):
    return calculate_avg_engagement(instagram_data, "content_group_name")


@register.simple_tag
def get_instagram_engagement_per_video_type(instagram_data):
    return calculate_avg_engagement(instagram_data, "video_type")


@register.simple_tag
def get_instagram_engagement_per_song_type(instagram_data):
    return calculate_avg_engagement(instagram_data, "song_type")


@register.simple_tag
def get_instagram_engagement_per_song_title(instagram_data):
    return calculate_avg_engagement(instagram_data, "song_title")


@register.simple_tag
def get_instagram_engagement_per_background(instagram_data):
    return calculate_avg_engagement(instagram_data, "background")


@register.simple_tag
def get_instagram_engagement_per_media_per_screen(instagram_data):
    return calculate_avg_engagement(instagram_data, "media_per_screen")


@register.simple_tag
def get_instagram_engagement_per_media_qty(instagram_data):
    return calculate_avg_engagement(instagram_data, "media_qty")


@register.simple_tag
def get_instagram_engagement_per_start_text(instagram_data):
    return calculate_avg_engagement(instagram_data, "used_start_text")


@register.simple_tag
def get_instagram_engagement_per_end_text(instagram_data):
    return calculate_avg_engagement(instagram_data, "used_end_text")


# Reusable function to calculate average watch percentage per category
def calculate_avg_watch_percentage_ig(instagram_data, category_key):
    category_watch = defaultdict(lambda: {"total_watch": 0, "count": 0})

    for reel_id, data in instagram_data.items():
        category = data.get(category_key, "Unknown")
        watch_time = data.get("ig_reels_avg_watch_time", 0)
        video_length = data.get("video_length", 1)  # Avoid division by zero

        # Calculate watch percentage
        watch_percentage = (watch_time / video_length) * 100 if video_length > 0 else 0

        # Sum watch percentages and count the number of reels per category
        category_watch[category]["total_watch"] += watch_percentage
        category_watch[category]["count"] += 1

    # Calculate average watch percentage per category
    avg_watch = {
        category: stats["total_watch"] / stats["count"]
        for category, stats in category_watch.items()
    }

    return {"labels": list(avg_watch.keys()), "values": list(avg_watch.values())}


# Template tags using the reusable function
@register.simple_tag
def get_instagram_avg_watch_percentage_per_content_group(instagram_data):
    return calculate_avg_watch_percentage_ig(instagram_data, "content_group_name")


@register.simple_tag
def get_instagram_avg_watch_percentage_per_video_type(instagram_data):
    return calculate_avg_watch_percentage_ig(instagram_data, "video_type")


@register.simple_tag
def get_instagram_avg_watch_percentage_per_song_type(instagram_data):
    return calculate_avg_watch_percentage_ig(instagram_data, "song_type")


@register.simple_tag
def get_instagram_avg_watch_percentage_per_song_title(instagram_data):
    return calculate_avg_watch_percentage_ig(instagram_data, "song_title")


@register.simple_tag
def get_instagram_avg_watch_percentage_per_background(instagram_data):
    return calculate_avg_watch_percentage_ig(instagram_data, "background")


@register.simple_tag
def get_instagram_avg_watch_percentage_per_media_per_screen(instagram_data):
    return calculate_avg_watch_percentage_ig(instagram_data, "media_per_screen")


@register.simple_tag
def get_instagram_avg_watch_percentage_per_media_qty(instagram_data):
    return calculate_avg_watch_percentage_ig(instagram_data, "media_qty")


@register.simple_tag
def get_instagram_avg_watch_percentage_per_start_text(instagram_data):
    return calculate_avg_watch_percentage_ig(instagram_data, "used_start_text")


@register.simple_tag
def get_instagram_avg_watch_percentage_per_end_text(instagram_data):
    return calculate_avg_watch_percentage_ig(instagram_data, "used_end_text")


# Add these template tags to your existing functions
@register.simple_tag
def get_instagram_video_length_vs_watch_time(instagram_data):
    scatter_data = [
        {"x": data["video_length"], "y": data["ig_reels_avg_watch_time"]}
        for data in instagram_data.values()
        if data.get("video_length") and data.get("ig_reels_avg_watch_time")
    ]
    return scatter_data


@register.simple_tag
def get_instagram_avg_views_per_daily_posts(instagram_data):
    reels_per_day = defaultdict(lambda: {"total_views": 0, "count": 0})

    # First calculate total views and count per day
    for data in instagram_data.values():
        uploaded_day = data.get("uploaded_day", "Unknown")
        views = data.get("views", 0)

        reels_per_day[uploaded_day]["total_views"] += views
        reels_per_day[uploaded_day]["count"] += 1

    # Then calculate average views per day
    avg_views_per_day = {
        day: stats["total_views"] / stats["count"]
        for day, stats in reels_per_day.items()
    }

    # Now group by number of reels posted per day
    reels_count_views = defaultdict(lambda: {"total_avg_views": 0, "count": 0})
    for day, avg_views in avg_views_per_day.items():
        num_reels = reels_per_day[day]["count"]
        reels_count_views[num_reels]["total_avg_views"] += avg_views
        reels_count_views[num_reels]["count"] += 1

    # Calculate final average views per reel count
    avg_views_per_reels_count = {
        num_reels: stats["total_avg_views"] / stats["count"]
        for num_reels, stats in reels_count_views.items()
    }

    # Sort by number of reels posted
    sorted_avg_views = sorted(avg_views_per_reels_count.items(), key=lambda x: x[0])

    return {
        "labels": [f"{item[0]} reels" for item in sorted_avg_views],
        "values": [item[1] for item in sorted_avg_views],
    }


@register.simple_tag
def get_instagram_views_per_day_of_week(instagram_data):
    day_of_week_views = defaultdict(lambda: {"total_views": 0, "count": 0})

    for data in instagram_data.values():
        uploaded_day = data.get("uploaded_day", "Unknown")
        views = data.get("views", 0)

        try:
            day = datetime.strptime(uploaded_day, "%Y-%m-%d").strftime("%A")
        except ValueError:
            day = "Unknown"

        day_of_week_views[day]["total_views"] += views
        day_of_week_views[day]["count"] += 1

    # Calculate averages and ensure all days are present
    avg_views_per_day = {
        day: stats["total_views"] / stats["count"] if stats["count"] > 0 else 0
        for day, stats in day_of_week_views.items()
    }

    # Ensure all days are present in order
    days_of_week = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    return {
        "labels": days_of_week,
        "values": [avg_views_per_day.get(day, 0) for day in days_of_week],
    }
