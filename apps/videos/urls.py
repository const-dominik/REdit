from django.urls import path
from apps.videos.views import VideoFormView


urlpatterns = [path("video-form/", VideoFormView.as_view(), name="video-form")]
