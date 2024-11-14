from django.urls import path
from videos.views import VideoFormView


urlpatterns = [path("video-form/", VideoFormView.as_view(), name="video-form")]
