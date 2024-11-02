from django.urls import path
from posts.views import SubredditList, ContentGroupList, PostsFormView, PostsView


urlpatterns = [
    path("", SubredditList.as_view(), name="subreddits"),
    path("groups/", ContentGroupList.as_view(), name="contentgroups"),
    path("posts-fetching/", PostsFormView.as_view(), name="posts-fetch"),
    path("posts/", PostsView.as_view(), name="my-posts"),
]
