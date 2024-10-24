from django.urls import path
from posts.views import SubredditList, ContentGroupList

urlpatterns = [
    path("", SubredditList.as_view(), name="subreddits"),
    path("groups/", ContentGroupList.as_view(), name="contentgroups"),
]
