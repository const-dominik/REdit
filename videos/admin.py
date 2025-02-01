from django.contrib import admin
from videos.models import UploadedVideo, GeneratedVideo


@admin.register(GeneratedVideo)
class GeneratedVideoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "content_group",
        "meta_data",
        "created_at",
    )
    search_fields = ("content_group__name",)


@admin.register(UploadedVideo)
class UploadedVideoAdmin(admin.ModelAdmin):
    list_display = (
        "video",
        "platform",
        "uploaded_video_id",
    )
    list_filter = ("platform",)
    search_fields = ("uploaded_video_id",)
