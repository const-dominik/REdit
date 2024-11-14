from django.db import models
from posts.models import ContentGroup


class GeneratedVideo(models.Model):
    video = models.FileField(upload_to="generated_videos/", null=True, blank=True)
    length = models.IntegerField(null=True, blank=True)
    content_group = models.ForeignKey(
        ContentGroup, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField()
