from django.db import models


class ContentGroup(models.Model):
    name = models.CharField(max_length=50, unique=True)
    subreddits = models.ManyToManyField("Subreddit", related_name="content_groups")

    def __str__(self):
        return self.name


class Subreddit(models.Model):
    name = models.CharField(max_length=50, unique=True)

    @property
    def url(self):
        return f"https://www.reddit.com/r/{self.name}/"

    def __str__(self):
        return self.url
