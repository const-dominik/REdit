# services/analytics_service.py
from statistics import mean
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from functools import lru_cache
import hashlib
import json

import numpy as np


class AnalyticsService:
    """
    Service class for calculating social media analytics.
    Handles YouTube and Instagram data processing.
    """

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

    def __init__(
        self,
        youtube_data=None,
        instagram_data=None,
        detailed_youtube_data=None,
        detailed_instagram_data=None,
    ):
        self.youtube_data = youtube_data
        self.instagram_data = instagram_data
        self.detailed_youtube_data = detailed_youtube_data
        self.detailed_instagram_data = detailed_instagram_data

    @staticmethod
    def safe_divide(
        numerator: Union[int, float], denominator: Union[int, float]
    ) -> float:
        """Safely divide two numbers, returning 0 if denominator is 0."""
        return numerator / denominator if denominator != 0 else 0

    @staticmethod
    def safe_get_field(
        data: Dict, field: str, default: Union[int, float] = 0
    ) -> Union[int, float]:
        """Safely get a field value with a default."""
        return data.get(field, default) if data else default

    def _make_cache_key(self, *args) -> str:
        """Create a cache key from arguments."""
        return hashlib.md5(
            json.dumps(args, sort_keys=True, default=str).encode()
        ).hexdigest()

    # Basic YouTube Analytics
    def get_youtube_basic_stats(self) -> Dict[str, Union[int, float]]:
        """Calculate basic YouTube stats from NumPy array data."""
        if self.youtube_data is None or len(self.youtube_data) == 0:
            return {
                "total_views": 0,
                "total_likes": 0,
                "total_comments": 0,
                "net_subscribers": 0,
                "total_minutes_watched": 0,
                "total_dislikes": 0,
                "avg_view_duration": 0.0,
                "avg_watch_percentage": 0.0,
            }

        try:
            gained = int(np.sum(self.youtube_data["subscribersGained"]))
            lost = int(np.sum(self.youtube_data["subscribersLost"]))

            return {
                "total_views": int(np.sum(self.youtube_data["views"])),
                "total_likes": int(np.sum(self.youtube_data["likes"])),
                "total_comments": int(np.sum(self.youtube_data["comments"])),
                "net_subscribers": gained - lost,
                "total_minutes_watched": int(
                    np.sum(self.youtube_data["estimatedMinutesWatched"])
                ),
                "total_dislikes": int(np.sum(self.youtube_data["dislikes"])),
                "avg_view_duration": round(
                    float(np.mean(self.youtube_data["averageViewDuration"])), 2
                ),
                "avg_watch_percentage": round(
                    float(np.mean(self.youtube_data["averageViewPercentage"])), 2
                ),
            }
        except (KeyError, IndexError, TypeError) as e:
            print(f"Error calculating YouTube stats: {e}")
            return {
                field: 0
                for field in [
                    "total_views",
                    "total_likes",
                    "total_comments",
                    "net_subscribers",
                    "total_minutes_watched",
                    "total_dislikes",
                    "avg_view_duration",
                    "avg_watch_percentage",
                ]
            }

    def get_youtube_chart_data(self) -> Dict[str, List]:
        """Get YouTube data formatted for charts."""
        if self.youtube_data is None or len(self.youtube_data) == 0:
            return {
                "days": [],
                "views": [],
                "likes": [],
                "comments": [],
                "shares": [],
                "avg_view_durations": [],
                "avg_watch_percentages": [],
                "subscribers_gained": [],
                "subscribers_lost": [],
                "minutes_watched": [],
                "dislikes": [],
            }

        try:
            return {
                "days": [str(day) for day in self.youtube_data["day"]],
                "views": [int(view) for view in self.youtube_data["views"]],
                "likes": [int(like) for like in self.youtube_data["likes"]],
                "comments": [int(comment) for comment in self.youtube_data["comments"]],
                "shares": [int(share) for share in self.youtube_data["shares"]],
                "avg_view_durations": [
                    float(duration)
                    for duration in self.youtube_data["averageViewDuration"]
                ],
                "avg_watch_percentages": [
                    float(percentage)
                    for percentage in self.youtube_data["averageViewPercentage"]
                ],
                "subscribers_gained": [
                    int(gained) for gained in self.youtube_data["subscribersGained"]
                ],
                "subscribers_lost": [
                    int(lost) for lost in self.youtube_data["subscribersLost"]
                ],
                "minutes_watched": [
                    int(minutes)
                    for minutes in self.youtube_data["estimatedMinutesWatched"]
                ],
                "dislikes": [int(dislike) for dislike in self.youtube_data["dislikes"]],
            }
        except (KeyError, IndexError, TypeError) as e:
            print(f"Error getting YouTube chart data: {e}")
            return {
                field: []
                for field in [
                    "days",
                    "views",
                    "likes",
                    "comments",
                    "shares",
                    "avg_view_durations",
                    "avg_watch_percentages",
                    "subscribers_gained",
                    "subscribers_lost",
                    "minutes_watched",
                    "dislikes",
                ]
            }

    def get_youtube_engagement_data(self) -> List[int]:
        """Calculate total engagement for YouTube over time."""
        if self.youtube_data is None or len(self.youtube_data) == 0:
            return []

        try:
            engagement_data = []
            for i in range(len(self.youtube_data)):
                total = (
                    int(self.youtube_data["likes"][i])
                    + int(self.youtube_data["comments"][i])
                    + int(self.youtube_data["shares"][i])
                )
                engagement_data.append(total)
            return engagement_data
        except (KeyError, IndexError, TypeError):
            return []

    # Instagram Basic Analytics
    def get_instagram_basic_stats(self) -> Dict[str, Union[int, float]]:
        """Get Instagram basic statistics."""
        if not self.instagram_data:
            return {
                "total_views": 0,
                "total_likes": 0,
                "total_comments": 0,
                "follower_count": 0,
                "accounts_reached": 0,
                "total_shares": 0,
                "total_engagements": 0,
                "avg_watch_percentage": 0.0,
                "total_minutes_watched": 0,
            }

        return {
            "total_views": self.safe_get_field(self.instagram_data, "views", 0),
            "total_likes": self.safe_get_field(self.instagram_data, "likes", 0),
            "total_comments": self.safe_get_field(self.instagram_data, "comments", 0),
            "follower_count": self.safe_get_field(
                self.instagram_data, "follower_count", 0
            ),
            "accounts_reached": self.safe_get_field(self.instagram_data, "reach", 0),
            "total_shares": self.safe_get_field(self.instagram_data, "shares", 0),
            "total_engagements": self.safe_get_field(
                self.instagram_data, "accounts_engaged", 0
            ),
            "avg_watch_percentage": self._calculate_instagram_avg_watch_time(),
            "total_minutes_watched": self._calculate_instagram_total_watch_time(),
        }

    def _calculate_instagram_avg_watch_time(self) -> float:
        """Calculate average watch time percentage for Instagram."""
        if not self.detailed_instagram_data:
            return 0.0

        total_percentage = 0.0
        count = 0

        for vid in self.detailed_instagram_data.values():
            watch_time = self.safe_get_field(vid, "ig_reels_avg_watch_time", 0)
            video_length = self.safe_get_field(vid, "video_length", 1)

            if video_length > 0:
                total_percentage += (watch_time / video_length) * 100
                count += 1

        return round(self.safe_divide(total_percentage, count), 2)

    def _calculate_instagram_total_watch_time(self) -> int:
        """Calculate total watch time for Instagram."""
        if not self.detailed_instagram_data:
            return 0

        return sum(
            self.safe_get_field(vid, "ig_reels_video_view_total_time", 0)
            for vid in self.detailed_instagram_data.values()
        )

    # Generic calculation methods
    def calculate_avg_views(
        self, data: Dict, category_key: str
    ) -> Optional[Dict[str, List]]:
        """Calculate average views per category."""
        if not data:
            return {"labels": [], "values": []}

        category_views = defaultdict(lambda: {"total_views": 0, "count": 0})

        for item_data in data.values():
            category = self.safe_get_field(item_data, category_key, "Unknown")
            views = self.safe_get_field(item_data, "views", 0)

            category_views[category]["total_views"] += views
            category_views[category]["count"] += 1

        if not category_views:
            return {"labels": [], "values": []}

        avg_views = {
            category: self.safe_divide(stats["total_views"], stats["count"])
            for category, stats in category_views.items()
        }

        return {"labels": list(avg_views.keys()), "values": list(avg_views.values())}

    def calculate_avg_engagement(
        self, data: Dict, category_key: str, platform: str = "youtube"
    ) -> Optional[Dict[str, Any]]:
        """Calculate average engagement per category."""
        if not data:
            return {"labels": [], "datasets": []}

        engagement_fields = ["likes", "comments", "shares"]
        if platform == "instagram":
            engagement_fields.append("saved")

        category_engagement = defaultdict(
            lambda: {field: 0 for field in engagement_fields + ["count"]}
        )

        for item_data in data.values():
            category = self.safe_get_field(item_data, category_key, "Unknown")

            for field in engagement_fields:
                category_engagement[category][field] += self.safe_get_field(
                    item_data, field, 0
                )
            category_engagement[category]["count"] += 1

        if not category_engagement:
            return {"labels": [], "datasets": []}

        # Calculate averages
        avg_engagement = {}
        for category, engagement in category_engagement.items():
            avg_engagement[category] = {
                field: self.safe_divide(engagement[field], engagement["count"])
                for field in engagement_fields
            }

        # Format for Chart.js
        labels = list(avg_engagement.keys())
        datasets = []

        for field in engagement_fields:
            datasets.append(
                {
                    "label": field.capitalize(),
                    "data": [
                        engagement[field] for engagement in avg_engagement.values()
                    ],
                    "backgroundColor": self.CHART_COLORS[field],
                }
            )

        return {"labels": labels, "datasets": datasets}

    def calculate_avg_watch_percentage(
        self, data: Dict, category_key: str, platform: str = "youtube"
    ) -> Optional[Dict[str, List]]:
        """Calculate average watch percentage per category."""
        if not data:
            return {"labels": [], "values": []}

        category_watch = defaultdict(lambda: {"total_watch": 0, "count": 0})

        for item_data in data.values():
            category = self.safe_get_field(item_data, category_key, "Unknown")

            if platform == "instagram":
                watch_time = self.safe_get_field(
                    item_data, "ig_reels_avg_watch_time", 0
                )
                video_length = self.safe_get_field(item_data, "video_length", 1)
                watch_percentage = self.safe_divide(watch_time, video_length) * 100
            else:  # YouTube
                watch_percentage = self.safe_get_field(
                    item_data, "averageViewPercentage", 0
                )

            category_watch[category]["total_watch"] += watch_percentage
            category_watch[category]["count"] += 1

        if not category_watch:
            return {"labels": [], "values": []}

        avg_watch = {
            category: self.safe_divide(stats["total_watch"], stats["count"])
            for category, stats in category_watch.items()
        }

        return {"labels": list(avg_watch.keys()), "values": list(avg_watch.values())}

    def calculate_text_usage_views(
        self, data: Dict, text_type: str
    ) -> Optional[Dict[str, List]]:
        """Calculate average views per text usage."""
        if not data:
            return {"labels": [], "values": []}

        text_usage_views = defaultdict(lambda: {"total_views": 0, "count": 0})

        for item_data in data.values():
            used_text = self.safe_get_field(item_data, f"used_{text_type}_text", False)
            views = self.safe_get_field(item_data, "views", 0)

            text_usage_views[used_text]["total_views"] += views
            text_usage_views[used_text]["count"] += 1

        if not text_usage_views:
            return {"labels": [], "values": []}

        avg_views = {
            ("Used" if used else "Not Used"): self.safe_divide(
                stats["total_views"], stats["count"]
            )
            for used, stats in text_usage_views.items()
        }

        return {"labels": list(avg_views.keys()), "values": list(avg_views.values())}

    def calculate_views_per_posting_frequency(
        self, data: Dict
    ) -> Optional[Dict[str, List]]:
        """Calculate average views based on posting frequency."""
        if not data:
            return {"labels": [], "values": []}

        posts_per_day = defaultdict(lambda: {"total_views": 0, "count": 0})

        for item_data in data.values():
            uploaded_day = self.safe_get_field(item_data, "uploaded_day", "Unknown")
            views = self.safe_get_field(item_data, "views", 0)

            posts_per_day[uploaded_day]["total_views"] += views
            posts_per_day[uploaded_day]["count"] += 1

        avg_views_per_day = {
            day: self.safe_divide(stats["total_views"], stats["count"])
            for day, stats in posts_per_day.items()
        }

        posts_count_views = defaultdict(lambda: {"total_avg_views": 0, "count": 0})
        for day, avg_views in avg_views_per_day.items():
            num_posts = posts_per_day[day]["count"]
            posts_count_views[num_posts]["total_avg_views"] += avg_views
            posts_count_views[num_posts]["count"] += 1

        avg_views_per_posts_count = {
            num_posts: self.safe_divide(stats["total_avg_views"], stats["count"])
            for num_posts, stats in posts_count_views.items()
        }

        if not avg_views_per_posts_count:
            return {"labels": [], "values": []}

        sorted_avg_views = sorted(avg_views_per_posts_count.items())

        return {
            "labels": [f"{item[0]} posts" for item in sorted_avg_views],
            "values": [item[1] for item in sorted_avg_views],
        }

    def calculate_views_per_day_of_week(self, data: Dict) -> Optional[Dict[str, List]]:
        """Calculate average views per day of the week."""
        if not data:
            return {"labels": self.DAYS_OF_WEEK, "values": [0] * 7}

        day_views = defaultdict(lambda: {"total_views": 0, "count": 0})

        for item_data in data.values():
            uploaded_day = self.safe_get_field(item_data, "uploaded_day", "Unknown")
            views = self.safe_get_field(item_data, "views", 0)

            try:
                day = datetime.strptime(uploaded_day, "%Y-%m-%d").strftime("%A")
            except (ValueError, TypeError):
                continue

            day_views[day]["total_views"] += views
            day_views[day]["count"] += 1

        avg_views_per_day = {
            day: self.safe_divide(
                day_views[day]["total_views"], day_views[day]["count"]
            )
            for day in self.DAYS_OF_WEEK
        }

        return {
            "labels": self.DAYS_OF_WEEK,
            "values": [avg_views_per_day[day] for day in self.DAYS_OF_WEEK],
        }

    def get_video_length_vs_view_metrics(
        self, data: Dict, platform: str = "youtube"
    ) -> Dict[str, List]:
        """Get video length vs view metrics for scatter plot."""
        if not data:
            if platform == "youtube":
                return {
                    "video_lengths": [],
                    "avg_view_percentages": [],
                    "avg_view_durations": [],
                }
            else:
                return []

        if platform == "youtube":
            video_lengths = []
            avg_view_percentages = []
            avg_view_durations = []

            for item_data in data.values():
                video_lengths.append(self.safe_get_field(item_data, "video_length", 0))
                avg_view_percentages.append(
                    self.safe_get_field(item_data, "averageViewPercentage", 0)
                )
                avg_view_durations.append(
                    self.safe_get_field(item_data, "averageViewDuration", 0)
                )

            return {
                "video_lengths": video_lengths,
                "avg_view_percentages": avg_view_percentages,
                "avg_view_durations": avg_view_durations,
            }
        else:  # Instagram
            return [
                {
                    "x": self.safe_get_field(data_item, "video_length", 0),
                    "y": self.safe_get_field(data_item, "ig_reels_avg_watch_time", 0),
                }
                for data_item in data.values()
                if self.safe_get_field(data_item, "video_length")
                and self.safe_get_field(data_item, "ig_reels_avg_watch_time")
            ]

    # Main aggregation methods
    def get_all_youtube_analytics(self) -> Dict[str, Any]:
        """Get all YouTube analytics in one call."""
        basic_stats = self.get_youtube_basic_stats()
        chart_data = self.get_youtube_chart_data()
        engagement_data = self.get_youtube_engagement_data()

        detailed_analytics = {
            "views_by_content_group": self.calculate_avg_views(
                self.detailed_youtube_data, "content_group_name"
            ),
            "views_by_video_type": self.calculate_avg_views(
                self.detailed_youtube_data, "video_type"
            ),
            "views_by_song_type": self.calculate_avg_views(
                self.detailed_youtube_data, "song_type"
            ),
            "views_by_song_title": self.calculate_avg_views(
                self.detailed_youtube_data, "song_title"
            ),
            "views_by_background": self.calculate_avg_views(
                self.detailed_youtube_data, "background"
            ),
            "views_by_media_per_screen": self.calculate_avg_views(
                self.detailed_youtube_data, "media_per_screen"
            ),
            "views_by_media_qty": self.calculate_avg_views(
                self.detailed_youtube_data, "media_qty"
            ),
            "views_by_start_text": self.calculate_text_usage_views(
                self.detailed_youtube_data, "start"
            ),
            "views_by_end_text": self.calculate_text_usage_views(
                self.detailed_youtube_data, "end"
            ),
            "engagement_by_content_group": self.calculate_avg_engagement(
                self.detailed_youtube_data, "content_group_name", "youtube"
            ),
            "engagement_by_video_type": self.calculate_avg_engagement(
                self.detailed_youtube_data, "video_type", "youtube"
            ),
            "engagement_by_song_type": self.calculate_avg_engagement(
                self.detailed_youtube_data, "song_type", "youtube"
            ),
            "engagement_by_song_title": self.calculate_avg_engagement(
                self.detailed_youtube_data, "song_title", "youtube"
            ),
            "engagement_by_background": self.calculate_avg_engagement(
                self.detailed_youtube_data, "background", "youtube"
            ),
            "engagement_by_media_per_screen": self.calculate_avg_engagement(
                self.detailed_youtube_data, "media_per_screen", "youtube"
            ),
            "engagement_by_media_qty": self.calculate_avg_engagement(
                self.detailed_youtube_data, "media_qty", "youtube"
            ),
            "engagement_by_start_text": self.calculate_avg_engagement(
                self.detailed_youtube_data, "used_start_text", "youtube"
            ),
            "engagement_by_end_text": self.calculate_avg_engagement(
                self.detailed_youtube_data, "used_end_text", "youtube"
            ),
            "watch_percentage_by_content_group": self.calculate_avg_watch_percentage(
                self.detailed_youtube_data, "content_group_name", "youtube"
            ),
            "watch_percentage_by_video_type": self.calculate_avg_watch_percentage(
                self.detailed_youtube_data, "video_type", "youtube"
            ),
            "watch_percentage_by_song_type": self.calculate_avg_watch_percentage(
                self.detailed_youtube_data, "song_type", "youtube"
            ),
            "watch_percentage_by_song_title": self.calculate_avg_watch_percentage(
                self.detailed_youtube_data, "song_title", "youtube"
            ),
            "watch_percentage_by_background": self.calculate_avg_watch_percentage(
                self.detailed_youtube_data, "background", "youtube"
            ),
            "watch_percentage_by_media_per_screen": self.calculate_avg_watch_percentage(
                self.detailed_youtube_data, "media_per_screen", "youtube"
            ),
            "watch_percentage_by_media_qty": self.calculate_avg_watch_percentage(
                self.detailed_youtube_data, "media_qty", "youtube"
            ),
            "watch_percentage_by_start_text": self.calculate_avg_watch_percentage(
                self.detailed_youtube_data, "used_start_text", "youtube"
            ),
            "watch_percentage_by_end_text": self.calculate_avg_watch_percentage(
                self.detailed_youtube_data, "used_end_text", "youtube"
            ),
            "video_length_vs_metrics": self.get_video_length_vs_view_metrics(
                self.detailed_youtube_data, "youtube"
            ),
            "views_per_posting_frequency": self.calculate_views_per_posting_frequency(
                self.detailed_youtube_data
            ),
            "views_per_day_of_week": self.calculate_views_per_day_of_week(
                self.detailed_youtube_data
            ),
        }

        return {
            "basic_stats": basic_stats,
            "chart_data": chart_data,
            "engagement_data": engagement_data,
            "detailed_analytics": detailed_analytics,
        }

    def get_all_instagram_analytics(self) -> Dict[str, Any]:
        """Get all Instagram analytics in one call."""
        basic_stats = self.get_instagram_basic_stats()

        detailed_analytics = {
            "views_by_content_group": self.calculate_avg_views(
                self.detailed_instagram_data, "content_group_name"
            ),
            "views_by_video_type": self.calculate_avg_views(
                self.detailed_instagram_data, "video_type"
            ),
            "views_by_song_type": self.calculate_avg_views(
                self.detailed_instagram_data, "song_type"
            ),
            "views_by_song_title": self.calculate_avg_views(
                self.detailed_instagram_data, "song_title"
            ),
            "views_by_background": self.calculate_avg_views(
                self.detailed_instagram_data, "background"
            ),
            "views_by_media_per_screen": self.calculate_avg_views(
                self.detailed_instagram_data, "media_per_screen"
            ),
            "views_by_media_qty": self.calculate_avg_views(
                self.detailed_instagram_data, "media_qty"
            ),
            "views_by_start_text": self.calculate_avg_views(
                self.detailed_instagram_data, "used_start_text"
            ),
            "views_by_end_text": self.calculate_avg_views(
                self.detailed_instagram_data, "used_end_text"
            ),
            "engagement_by_content_group": self.calculate_avg_engagement(
                self.detailed_instagram_data, "content_group_name", "instagram"
            ),
            "engagement_by_video_type": self.calculate_avg_engagement(
                self.detailed_instagram_data, "video_type", "instagram"
            ),
            "engagement_by_song_type": self.calculate_avg_engagement(
                self.detailed_instagram_data, "song_type", "instagram"
            ),
            "engagement_by_song_title": self.calculate_avg_engagement(
                self.detailed_instagram_data, "song_title", "instagram"
            ),
            "engagement_by_background": self.calculate_avg_engagement(
                self.detailed_instagram_data, "background", "instagram"
            ),
            "engagement_by_media_per_screen": self.calculate_avg_engagement(
                self.detailed_instagram_data, "media_per_screen", "instagram"
            ),
            "engagement_by_media_qty": self.calculate_avg_engagement(
                self.detailed_instagram_data, "media_qty", "instagram"
            ),
            "engagement_by_start_text": self.calculate_avg_engagement(
                self.detailed_instagram_data, "used_start_text", "instagram"
            ),
            "engagement_by_end_text": self.calculate_avg_engagement(
                self.detailed_instagram_data, "used_end_text", "instagram"
            ),
            "watch_percentage_by_content_group": self.calculate_avg_watch_percentage(
                self.detailed_instagram_data, "content_group_name", "instagram"
            ),
            "watch_percentage_by_video_type": self.calculate_avg_watch_percentage(
                self.detailed_instagram_data, "video_type", "instagram"
            ),
            "watch_percentage_by_song_type": self.calculate_avg_watch_percentage(
                self.detailed_instagram_data, "song_type", "instagram"
            ),
            "watch_percentage_by_song_title": self.calculate_avg_watch_percentage(
                self.detailed_instagram_data, "song_title", "instagram"
            ),
            "watch_percentage_by_background": self.calculate_avg_watch_percentage(
                self.detailed_instagram_data, "background", "instagram"
            ),
            "watch_percentage_by_media_per_screen": self.calculate_avg_watch_percentage(
                self.detailed_instagram_data, "media_per_screen", "instagram"
            ),
            "watch_percentage_by_media_qty": self.calculate_avg_watch_percentage(
                self.detailed_instagram_data, "media_qty", "instagram"
            ),
            "watch_percentage_by_start_text": self.calculate_avg_watch_percentage(
                self.detailed_instagram_data, "used_start_text", "instagram"
            ),
            "watch_percentage_by_end_text": self.calculate_avg_watch_percentage(
                self.detailed_instagram_data, "used_end_text", "instagram"
            ),
            "video_length_vs_watch_time": self.get_video_length_vs_view_metrics(
                self.detailed_instagram_data, "instagram"
            ),
            "views_per_posting_frequency": self.calculate_views_per_posting_frequency(
                self.detailed_instagram_data
            ),
            "views_per_day_of_week": self.calculate_views_per_day_of_week(
                self.detailed_instagram_data
            ),
        }

        return {"basic_stats": basic_stats, "detailed_analytics": detailed_analytics}
