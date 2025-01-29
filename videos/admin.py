from django.contrib import admin
from videos.models import UploadedVideo, GeneratedVideo


# Register your models here.
@admin.register(GeneratedVideo)
class GeneratedVideoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "content_group",
        "created_at",
    )  # Customize the fields displayed in the admin list view
    search_fields = ("content_group__name",)  # Adjust based on your ContentGroup model


@admin.register(UploadedVideo)
class UploadedVideoAdmin(admin.ModelAdmin):
    list_display = (
        "video",
        "platform",
        "uploaded_video_id",
    )  # Customize fields here too
    list_filter = ("platform",)  # Add filter options
    search_fields = ("uploaded_video_id",)  # Enable searching by uploaded_video_id
