import datetime
import os

from django.db import models
from posts.models import ContentGroup, Post


def randomize_name(instance, filename):
    ext = filename.split(".")[-1]
    unique_filename = f"{int(datetime.datetime.now().timestamp() * 1000)}.{ext}"

    return os.path.join("generated_videos/", unique_filename)


class GeneratedVideo(models.Model):
    video = models.FileField(upload_to=randomize_name, null=True, blank=True)
    content_group = models.ForeignKey(
        ContentGroup, on_delete=models.SET_NULL, null=True, blank=True
    )
    used_media = models.ManyToManyField(Post, related_name="generated_videos")
    meta_data = models.JSONField("metadata", default=dict)
    created_at = models.DateTimeField()
