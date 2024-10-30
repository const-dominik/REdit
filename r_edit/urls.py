from django.contrib import admin
from django.urls import path, include

from rest_framework import routers
from posts.views import SubredditViewSet, ContentGroupViewSet

router = routers.SimpleRouter()
router.register(r"subreddits", SubredditViewSet)
router.register(r"groups", ContentGroupViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("dashboard/", include("dashboard.urls"), name="dashboard"),
    path("subreddits/", include("posts.urls"), name="posts"),
    path("__reload__/", include("django_browser_reload.urls")),
    path("api/", include(router.urls)),
]
