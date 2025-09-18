from rest_framework import serializers
from apps.posts.models import ContentGroup, Subreddit


class SubredditSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Subreddit
        fields = ["name"]


class ContentGroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ContentGroup
        fields = ["name"]
