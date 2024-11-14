from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

from rest_framework import routers
from posts.views import SubredditViewSet, ContentGroupViewSet, PostsView

router = routers.SimpleRouter()
router.register(r"subreddits", SubredditViewSet)
router.register(r"groups", ContentGroupViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(url="/dashboard/", permanent=True)),
    path("dashboard/", include("dashboard.urls"), name="dashboard"),
    path("subreddits/", include("posts.urls"), name="posts"),
    path("videos/", include("videos.urls"), name="videos"),
    path("__reload__/", include("django_browser_reload.urls")),
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
