from django.contrib import admin
from apps.posts.models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("subreddit", "title", "content", "post_id", "id", "video")
