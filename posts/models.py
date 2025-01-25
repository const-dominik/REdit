from django.db import models
from datetime import datetime
from django.core.validators import MinValueValidator, MaxValueValidator


class Subreddit(models.Model):
    class Type(models.TextChoices):
        IMAGE = "img"  # memes, cute animals
        VIDEO = "vid"  # memes, cute animals also, satisfying stuff
        TEXT = "text"  # amitheasshole, showerthoughts

    types = models.CharField(
        max_length=20
    )  # fetching posts, what kind of stuff do we want from this subreddit?

    name = models.CharField(max_length=50, unique=True)
    last_checked = models.DateField(default=datetime(2020, 1, 1))

    def set_types(self, type_list):
        self.types = ",".join(type_list)

    def get_types(self):
        return self.types.split(",") if self.types else []

    def toggle_type(self, type):
        types = self.get_types()

        removed_flag = True

        if type in types:
            types.remove(type)
        else:
            types.append(type)
            removed_flag = False

        self.set_types(types)

        return removed_flag

    @property
    def url(self):
        return f"https://www.reddit.com/r/{self.name}/"

    def __str__(self):
        return f"r/{self.name}"


class ContentGroup(models.Model):
    class Backgrounds(models.TextChoices):
        BLACK = "black"
        MINECRAFT = "minecraft"
        SUBWAY = "subway"
        NOTBLACK = "not-black"

    name = models.CharField(max_length=50, unique=True)
    subreddits = models.ManyToManyField("Subreddit", related_name="content_groups")
    start_text = models.CharField(max_length=50, default="")
    end_text = models.CharField(max_length=50, default="")
    media_per_video = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(500)], default=1
    )
    type = models.CharField(
        max_length=4, choices=Subreddit.Type.choices, default=Subreddit.Type.IMAGE
    )
    media_per_screen = models.IntegerField(choices=[(1, "one"), (2, "two")], default=1)
    background = models.CharField(
        max_length=10,
        choices=Backgrounds.choices,
        default="minecraft",
    )

    def __str__(self):
        return self.name


class Post(models.Model):
    post_id = models.CharField(max_length=50, unique=True)
    subreddit = models.ForeignKey(Subreddit, on_delete=models.CASCADE)
    title = models.CharField(max_length=300)
    content = models.CharField(max_length=4000, blank=True, null=True)
    image = models.ImageField(upload_to="images/", null=True, blank=True)
    video = models.FileField(upload_to="videos/", null=True, blank=True)
    posted_at = models.DateTimeField()
    author = models.CharField(max_length=50)
