from django.urls import path
from apps.posts.views import (
    SubredditList,
    ContentGroupList,
    PostsFormView,
    get_song_titles,
)


urlpatterns = [
    path("", SubredditList.as_view(), name="subreddits"),
    path("groups/", ContentGroupList.as_view(), name="contentgroups"),
    path("posts-fetching/", PostsFormView.as_view(), name="posts-fetch"),
    path("ajax/song_titles/", get_song_titles, name="ajax_song_titles"),
]
