from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

from rest_framework import routers
from apps.posts.views import SubredditViewSet, ContentGroupViewSet

router = routers.SimpleRouter()
router.register(r"subreddits", SubredditViewSet)
router.register(r"groups", ContentGroupViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(url="/dashboard/", permanent=True)),
    path("dashboard/", include("apps.dashboard.urls"), name="dashboard"),
    path("subreddits/", include("apps.posts.urls"), name="posts"),
    path("videos/", include("apps.videos.urls"), name="videos"),
    path("__reload__/", include("django_browser_reload.urls")),
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
