from django import template
from statistics import mean
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

import numpy as np

register = template.Library()

# Constants
DAYS_OF_WEEK = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
FIELD_INDICES = {"likes": 3, "comments": 2, "shares": 5}
CHART_COLORS = {
    "likes": "rgba(255, 99, 132, 0.6)",
    "comments": "rgba(54, 162, 235, 0.6)",
    "shares": "rgba(75, 192, 192, 0.6)",
    "saved": "rgba(153, 102, 255, 0.6)",
}


def safe_divide(numerator: Union[int, float], denominator: Union[int, float]) -> float:
    """Safely divide two numbers, returning 0 if denominator is 0."""
    return numerator / denominator if denominator != 0 else 0


def safe_get_field(
    data: Dict, field: str, default: Union[int, float] = 0
) -> Union[int, float]:
    """Safely get a field value with a default."""
    return data.get(field, default)


# Basic filters for NumPy arrays
@register.filter
def sum_by_field(data, field: str) -> int:
    """Sum a field in the NumPy structured array."""
    if data is None or len(data) == 0:
        return 0
    try:
        return int(np.sum(data[field]))
    except (KeyError, IndexError, TypeError):
        return 0


@register.filter
def pluck_field(data, field: str) -> List:
    """Extract a field from the NumPy structured array as a list."""
    if data is None or len(data) == 0:
        return []
    try:
        return list(data[field])
    except (KeyError, IndexError, TypeError):
        return []


@register.filter
def net_subscribers(data, fields: str) -> int:
    """Calculate net subscribers gained/lost."""
    if data is None or len(data) == 0 or not fields:
        return 0
    try:
        field1, field2 = fields.split(",")
        gained = int(np.sum(data[field1]))
        lost = int(np.sum(data[field2]))
        return gained - lost
    except (ValueError, KeyError, IndexError, TypeError):
        return 0


@register.filter
def total_engagement(data, fields: str) -> List[int]:
    """Calculate total engagement by summing specified fields over time."""
    if data is None or len(data) == 0 or not fields:
        return []

    try:
        field_list = fields.split(",")
        engagement_data = []

        for item in data:
            total = 0
            for field in field_list:
                if field in FIELD_INDICES:
                    index = FIELD_INDICES[field]
                    total += max(int(item[index]), 0)
            engagement_data.append(total)

        return engagement_data
    except (ValueError, KeyError, IndexError, TypeError):
        return []


@register.filter
def average(data, field: str) -> float:
    """Calculate average of a field."""
    if data is None or len(data) == 0:
        return 0.0
    try:
        values = data[field]
        return round(mean(values), 2) if values else 0.0
    except (KeyError, IndexError, TypeError, ZeroDivisionError):
        return 0.0


@register.filter
def average_watch_time(data: Dict) -> float:
    """Calculate average watch time percentage."""
    if not data:
        return 0.0

    total_percentage = 0.0
    count = 0

    for vid in data.values():
        watch_time = safe_get_field(vid, "ig_reels_avg_watch_time", 0)
        video_length = safe_get_field(vid, "video_length", 1)

        if video_length > 0:
            total_percentage += (watch_time / video_length) * 100
            count += 1

    return round(safe_divide(total_percentage, count), 2)


@register.filter
def watch_in_total(data: Dict) -> int:
    """Calculate total watch time across all videos."""
    if not data:
        return 0

    return sum(
        safe_get_field(vid, "ig_reels_video_view_total_time", 0)
        for vid in data.values()
    )


@register.filter
def get_item(dictionary: Dict, key: str) -> Any:
    """Get item from dictionary safely."""
    return dictionary.get(key) if dictionary else None


# Generic calculation functions
def calculate_avg_views(data: Dict, category_key: str) -> Optional[Dict[str, List]]:
    """Calculate average views per category."""
    if not data:
        return None

    category_views = defaultdict(lambda: {"total_views": 0, "count": 0})

    for item_data in data.values():
        category = safe_get_field(item_data, category_key, "Unknown")
        views = safe_get_field(item_data, "views", 0)

        category_views[category]["total_views"] += views
        category_views[category]["count"] += 1

    if not category_views:
        return {"labels": [], "values": []}

    avg_views = {
        category: safe_divide(stats["total_views"], stats["count"])
        for category, stats in category_views.items()
    }

    return {"labels": list(avg_views.keys()), "values": list(avg_views.values())}


def calculate_avg_engagement(
    data: Dict, category_key: str, platform: str = "youtube"
) -> Optional[Dict[str, Any]]:
    """Calculate average engagement per category for different platforms."""
    if not data:
        return None

    engagement_fields = ["likes", "comments", "shares"]
    if platform == "instagram":
        engagement_fields.append("saved")

    category_engagement = defaultdict(
        lambda: {field: 0 for field in engagement_fields + ["count"]}
    )

    for item_data in data.values():
        category = safe_get_field(item_data, category_key, "Unknown")

        for field in engagement_fields:
            category_engagement[category][field] += safe_get_field(item_data, field, 0)
        category_engagement[category]["count"] += 1

    if not category_engagement:
        return {"labels": [], "datasets": []}

    # Calculate averages
    avg_engagement = {}
    for category, engagement in category_engagement.items():
        avg_engagement[category] = {
            field: safe_divide(engagement[field], engagement["count"])
            for field in engagement_fields
        }

    # Format for Chart.js
    labels = list(avg_engagement.keys())
    datasets = []

    for field in engagement_fields:
        datasets.append(
            {
                "label": field.capitalize(),
                "data": [engagement[field] for engagement in avg_engagement.values()],
                "backgroundColor": CHART_COLORS[field],
            }
        )

    return {"labels": labels, "datasets": datasets}


def calculate_avg_watch_percentage(
    data: Dict, category_key: str, platform: str = "youtube"
) -> Optional[Dict[str, List]]:
    """Calculate average watch percentage per category."""
    if not data:
        return None

    category_watch = defaultdict(lambda: {"total_watch": 0, "count": 0})

    for item_data in data.values():
        category = safe_get_field(item_data, category_key, "Unknown")

        if platform == "instagram":
            watch_time = safe_get_field(item_data, "ig_reels_avg_watch_time", 0)
            video_length = safe_get_field(item_data, "video_length", 1)
            watch_percentage = safe_divide(watch_time, video_length) * 100
        else:  # YouTube
            watch_percentage = safe_get_field(item_data, "averageViewPercentage", 0)

        category_watch[category]["total_watch"] += watch_percentage
        category_watch[category]["count"] += 1

    if not category_watch:
        return {"labels": [], "values": []}

    avg_watch = {
        category: safe_divide(stats["total_watch"], stats["count"])
        for category, stats in category_watch.items()
    }

    return {"labels": list(avg_watch.keys()), "values": list(avg_watch.values())}


def calculate_text_usage_views(data: Dict, text_type: str) -> Optional[Dict[str, List]]:
    """Calculate average views per text usage (used/not used)."""
    if not data:
        return None

    text_usage_views = defaultdict(lambda: {"total_views": 0, "count": 0})

    for item_data in data.values():
        used_text = safe_get_field(item_data, f"used_{text_type}_text", False)
        views = safe_get_field(item_data, "views", 0)

        text_usage_views[used_text]["total_views"] += views
        text_usage_views[used_text]["count"] += 1

    if not text_usage_views:
        return {"labels": [], "values": []}

    avg_views = {
        ("Used" if used else "Not Used"): safe_divide(
            stats["total_views"], stats["count"]
        )
        for used, stats in text_usage_views.items()
    }

    return {"labels": list(avg_views.keys()), "values": list(avg_views.values())}


def calculate_views_per_posting_frequency(data: Dict) -> Optional[Dict[str, List]]:
    """Calculate average views based on number of posts per day."""
    if not data:
        return None

    posts_per_day = defaultdict(lambda: {"total_views": 0, "count": 0})

    # Group by day and calculate total views per day
    for item_data in data.values():
        uploaded_day = safe_get_field(item_data, "uploaded_day", "Unknown")
        views = safe_get_field(item_data, "views", 0)

        posts_per_day[uploaded_day]["total_views"] += views
        posts_per_day[uploaded_day]["count"] += 1

    # Calculate average views per day
    avg_views_per_day = {
        day: safe_divide(stats["total_views"], stats["count"])
        for day, stats in posts_per_day.items()
    }

    # Group by number of posts per day
    posts_count_views = defaultdict(lambda: {"total_avg_views": 0, "count": 0})
    for day, avg_views in avg_views_per_day.items():
        num_posts = posts_per_day[day]["count"]
        posts_count_views[num_posts]["total_avg_views"] += avg_views
        posts_count_views[num_posts]["count"] += 1

    # Calculate final averages
    avg_views_per_posts_count = {
        num_posts: safe_divide(stats["total_avg_views"], stats["count"])
        for num_posts, stats in posts_count_views.items()
    }

    if not avg_views_per_posts_count:
        return {"labels": [], "values": []}

    sorted_avg_views = sorted(avg_views_per_posts_count.items())

    return {
        "labels": [f"{item[0]} posts" for item in sorted_avg_views],
        "values": [item[1] for item in sorted_avg_views],
    }


def calculate_views_per_day_of_week(data: Dict) -> Optional[Dict[str, List]]:
    """Calculate average views per day of the week."""
    if not data:
        return None

    day_views = defaultdict(lambda: {"total_views": 0, "count": 0})

    for item_data in data.values():
        uploaded_day = safe_get_field(item_data, "uploaded_day", "Unknown")
        views = safe_get_field(item_data, "views", 0)

        try:
            day = datetime.strptime(uploaded_day, "%Y-%m-%d").strftime("%A")
        except (ValueError, TypeError):
            continue  # Skip invalid dates

        day_views[day]["total_views"] += views
        day_views[day]["count"] += 1

    # Calculate averages for all days
    avg_views_per_day = {
        day: safe_divide(day_views[day]["total_views"], day_views[day]["count"])
        for day in DAYS_OF_WEEK
    }

    return {
        "labels": DAYS_OF_WEEK,
        "values": [avg_views_per_day[day] for day in DAYS_OF_WEEK],
    }


# YouTube Shorts template tags
@register.simple_tag
def get_views_distribution_by_content_group(
    detailed_yt_shorts: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_views(detailed_yt_shorts, "content_group_name")


@register.simple_tag
def get_engagement_rate_by_content_group(
    detailed_yt_shorts: Dict,
) -> Optional[Dict[str, Any]]:
    return calculate_avg_engagement(detailed_yt_shorts, "content_group_name", "youtube")


@register.simple_tag
def get_avg_views_per_video_type(detailed_yt_shorts: Dict) -> Optional[Dict[str, List]]:
    return calculate_avg_views(detailed_yt_shorts, "video_type")


@register.simple_tag
def get_avg_views_per_song_type(detailed_yt_shorts: Dict) -> Optional[Dict[str, List]]:
    return calculate_avg_views(detailed_yt_shorts, "song_type")


@register.simple_tag
def get_avg_views_per_song_title(detailed_yt_shorts: Dict) -> Optional[Dict[str, List]]:
    return calculate_avg_views(detailed_yt_shorts, "song_title")


@register.simple_tag
def get_avg_views_per_background(detailed_yt_shorts: Dict) -> Optional[Dict[str, List]]:
    return calculate_avg_views(detailed_yt_shorts, "background")


@register.simple_tag
def get_avg_views_per_media_per_screen(
    detailed_yt_shorts: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_views(detailed_yt_shorts, "media_per_screen")


@register.simple_tag
def get_avg_views_per_media_qty(detailed_yt_shorts: Dict) -> Optional[Dict[str, List]]:
    return calculate_avg_views(detailed_yt_shorts, "media_qty")


@register.simple_tag
def get_avg_views_per_text_usage(
    detailed_yt_shorts: Dict, text_type: str
) -> Optional[Dict[str, List]]:
    return calculate_text_usage_views(detailed_yt_shorts, text_type)


# YouTube engagement tags
@register.simple_tag
def get_avg_engagement_per_video_type(
    detailed_yt_shorts: Dict,
) -> Optional[Dict[str, Any]]:
    return calculate_avg_engagement(detailed_yt_shorts, "video_type", "youtube")


@register.simple_tag
def get_avg_engagement_per_song_type(
    detailed_yt_shorts: Dict,
) -> Optional[Dict[str, Any]]:
    return calculate_avg_engagement(detailed_yt_shorts, "song_type", "youtube")


@register.simple_tag
def get_avg_engagement_per_song_title(
    detailed_yt_shorts: Dict,
) -> Optional[Dict[str, Any]]:
    return calculate_avg_engagement(detailed_yt_shorts, "song_title", "youtube")


@register.simple_tag
def get_avg_engagement_per_background(
    detailed_yt_shorts: Dict,
) -> Optional[Dict[str, Any]]:
    return calculate_avg_engagement(detailed_yt_shorts, "background", "youtube")


@register.simple_tag
def get_avg_engagement_per_media_per_screen(
    detailed_yt_shorts: Dict,
) -> Optional[Dict[str, Any]]:
    return calculate_avg_engagement(detailed_yt_shorts, "media_per_screen", "youtube")


@register.simple_tag
def get_avg_engagement_per_media_qty(
    detailed_yt_shorts: Dict,
) -> Optional[Dict[str, Any]]:
    return calculate_avg_engagement(detailed_yt_shorts, "media_qty", "youtube")


@register.simple_tag
def get_avg_engagement_per_start_text(
    detailed_yt_shorts: Dict,
) -> Optional[Dict[str, Any]]:
    return calculate_avg_engagement(detailed_yt_shorts, "used_start_text", "youtube")


@register.simple_tag
def get_avg_engagement_per_end_text(
    detailed_yt_shorts: Dict,
) -> Optional[Dict[str, Any]]:
    return calculate_avg_engagement(detailed_yt_shorts, "used_end_text", "youtube")


# YouTube watch percentage tags
@register.simple_tag
def get_avg_watch_percentage_per_content_group(
    detailed_yt_shorts: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_watch_percentage(
        detailed_yt_shorts, "content_group_name", "youtube"
    )


@register.simple_tag
def get_avg_watch_percentage_per_video_type(
    detailed_yt_shorts: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_watch_percentage(detailed_yt_shorts, "video_type", "youtube")


@register.simple_tag
def get_avg_watch_percentage_per_song_type(
    detailed_yt_shorts: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_watch_percentage(detailed_yt_shorts, "song_type", "youtube")


@register.simple_tag
def get_avg_watch_percentage_per_song_title(
    detailed_yt_shorts: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_watch_percentage(detailed_yt_shorts, "song_title", "youtube")


@register.simple_tag
def get_avg_watch_percentage_per_background(
    detailed_yt_shorts: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_watch_percentage(detailed_yt_shorts, "background", "youtube")


@register.simple_tag
def get_avg_watch_percentage_per_media_per_screen(
    detailed_yt_shorts: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_watch_percentage(
        detailed_yt_shorts, "media_per_screen", "youtube"
    )


@register.simple_tag
def get_avg_watch_percentage_per_media_qty(
    detailed_yt_shorts: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_watch_percentage(detailed_yt_shorts, "media_qty", "youtube")


@register.simple_tag
def get_avg_watch_percentage_per_start_text(
    detailed_yt_shorts: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_watch_percentage(
        detailed_yt_shorts, "used_start_text", "youtube"
    )


@register.simple_tag
def get_avg_watch_percentage_per_end_text(
    detailed_yt_shorts: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_watch_percentage(
        detailed_yt_shorts, "used_end_text", "youtube"
    )


# YouTube analytics tags
@register.simple_tag
def get_video_length_vs_view_metrics(detailed_yt_shorts: Dict) -> Dict[str, List]:
    """Get video length vs view metrics for scatter plot."""
    if not detailed_yt_shorts:
        return {
            "video_lengths": [],
            "avg_view_percentages": [],
            "avg_view_durations": [],
        }

    video_lengths = []
    avg_view_percentages = []
    avg_view_durations = []

    for item_data in detailed_yt_shorts.values():
        video_lengths.append(safe_get_field(item_data, "video_length", 0))
        avg_view_percentages.append(
            safe_get_field(item_data, "averageViewPercentage", 0)
        )
        avg_view_durations.append(safe_get_field(item_data, "averageViewDuration", 0))

    return {
        "video_lengths": video_lengths,
        "avg_view_percentages": avg_view_percentages,
        "avg_view_durations": avg_view_durations,
    }


@register.simple_tag
def get_avg_views_per_shorts_posted(
    detailed_yt_shorts: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_views_per_posting_frequency(detailed_yt_shorts)


@register.simple_tag
def get_avg_views_per_day_of_week(
    detailed_yt_shorts: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_views_per_day_of_week(detailed_yt_shorts)


# Instagram template tags (using the same generic functions)
@register.simple_tag
def get_instagram_avg_views_per_content_group(
    instagram_data: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_views(instagram_data, "content_group_name")


@register.simple_tag
def get_instagram_avg_views_per_video_type(
    instagram_data: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_views(instagram_data, "video_type")


@register.simple_tag
def get_instagram_avg_views_per_song_type(
    instagram_data: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_views(instagram_data, "song_type")


@register.simple_tag
def get_instagram_avg_views_per_song_title(
    instagram_data: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_views(instagram_data, "song_title")


@register.simple_tag
def get_instagram_avg_views_per_background(
    instagram_data: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_views(instagram_data, "background")


@register.simple_tag
def get_instagram_avg_views_per_media_per_screen(
    instagram_data: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_views(instagram_data, "media_per_screen")


@register.simple_tag
def get_instagram_avg_views_per_media_qty(
    instagram_data: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_views(instagram_data, "media_qty")


@register.simple_tag
def get_instagram_avg_views_per_start_text(
    instagram_data: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_views(instagram_data, "used_start_text")


@register.simple_tag
def get_instagram_avg_views_per_end_text(
    instagram_data: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_views(instagram_data, "used_end_text")


# Instagram engagement tags
@register.simple_tag
def get_instagram_engagement_per_content_group(
    instagram_data: Dict,
) -> Optional[Dict[str, Any]]:
    return calculate_avg_engagement(instagram_data, "content_group_name", "instagram")


@register.simple_tag
def get_instagram_engagement_per_video_type(
    instagram_data: Dict,
) -> Optional[Dict[str, Any]]:
    return calculate_avg_engagement(instagram_data, "video_type", "instagram")


@register.simple_tag
def get_instagram_engagement_per_song_type(
    instagram_data: Dict,
) -> Optional[Dict[str, Any]]:
    return calculate_avg_engagement(instagram_data, "song_type", "instagram")


@register.simple_tag
def get_instagram_engagement_per_song_title(
    instagram_data: Dict,
) -> Optional[Dict[str, Any]]:
    return calculate_avg_engagement(instagram_data, "song_title", "instagram")


@register.simple_tag
def get_instagram_engagement_per_background(
    instagram_data: Dict,
) -> Optional[Dict[str, Any]]:
    return calculate_avg_engagement(instagram_data, "background", "instagram")


@register.simple_tag
def get_instagram_engagement_per_media_per_screen(
    instagram_data: Dict,
) -> Optional[Dict[str, Any]]:
    return calculate_avg_engagement(instagram_data, "media_per_screen", "instagram")


@register.simple_tag
def get_instagram_engagement_per_media_qty(
    instagram_data: Dict,
) -> Optional[Dict[str, Any]]:
    return calculate_avg_engagement(instagram_data, "media_qty", "instagram")


@register.simple_tag
def get_instagram_engagement_per_start_text(
    instagram_data: Dict,
) -> Optional[Dict[str, Any]]:
    return calculate_avg_engagement(instagram_data, "used_start_text", "instagram")


@register.simple_tag
def get_instagram_engagement_per_end_text(
    instagram_data: Dict,
) -> Optional[Dict[str, Any]]:
    return calculate_avg_engagement(instagram_data, "used_end_text", "instagram")


# Instagram watch percentage tags
@register.simple_tag
def get_instagram_avg_watch_percentage_per_content_group(
    instagram_data: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_watch_percentage(
        instagram_data, "content_group_name", "instagram"
    )


@register.simple_tag
def get_instagram_avg_watch_percentage_per_video_type(
    instagram_data: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_watch_percentage(instagram_data, "video_type", "instagram")


@register.simple_tag
def get_instagram_avg_watch_percentage_per_song_type(
    instagram_data: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_watch_percentage(instagram_data, "song_type", "instagram")


@register.simple_tag
def get_instagram_avg_watch_percentage_per_song_title(
    instagram_data: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_watch_percentage(instagram_data, "song_title", "instagram")


@register.simple_tag
def get_instagram_avg_watch_percentage_per_background(
    instagram_data: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_watch_percentage(instagram_data, "background", "instagram")


@register.simple_tag
def get_instagram_avg_watch_percentage_per_media_per_screen(
    instagram_data: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_watch_percentage(
        instagram_data, "media_per_screen", "instagram"
    )


@register.simple_tag
def get_instagram_avg_watch_percentage_per_media_qty(
    instagram_data: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_watch_percentage(instagram_data, "media_qty", "instagram")


@register.simple_tag
def get_instagram_avg_watch_percentage_per_start_text(
    instagram_data: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_watch_percentage(
        instagram_data, "used_start_text", "instagram"
    )


@register.simple_tag
def get_instagram_avg_watch_percentage_per_end_text(
    instagram_data: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_avg_watch_percentage(instagram_data, "used_end_text", "instagram")


# Instagram analytics tags
@register.simple_tag
def get_instagram_video_length_vs_watch_time(
    instagram_data: Dict,
) -> List[Dict[str, float]]:
    """Get Instagram video length vs watch time for scatter plot."""
    if not instagram_data:
        return []

    return [
        {
            "x": safe_get_field(data, "video_length", 0),
            "y": safe_get_field(data, "ig_reels_avg_watch_time", 0),
        }
        for data in instagram_data.values()
        if safe_get_field(data, "video_length")
        and safe_get_field(data, "ig_reels_avg_watch_time")
    ]


@register.simple_tag
def get_instagram_avg_views_per_daily_posts(
    instagram_data: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_views_per_posting_frequency(instagram_data)


@register.simple_tag
def get_instagram_views_per_day_of_week(
    instagram_data: Dict,
) -> Optional[Dict[str, List]]:
    return calculate_views_per_day_of_week(instagram_data)
