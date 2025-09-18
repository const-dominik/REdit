from django import forms
from apps.posts.models import ContentGroup, Subreddit
from django_select2.forms import Select2Widget
from django.conf import settings

import re
import os

AUDIO_PATH = settings.STATIC_ROOT + "/video_assets/audios/"


def get_song_types():
    """Fetch available song types (folders in AUDIO_PATH)."""
    if os.path.exists(AUDIO_PATH):
        return [
            (folder, folder)
            for folder in os.listdir(AUDIO_PATH)
            if os.path.isdir(os.path.join(AUDIO_PATH, folder))
        ]
    return []


class ContentGroupForm(forms.ModelForm):
    start_text = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Start Text"}
        ),
    )
    end_text = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "End Text"}
        ),
    )

    song_type = forms.ChoiceField(
        required=False,
        choices=get_song_types,
        widget=forms.Select(
            attrs={
                "class": "w-full border border-blue-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-300 focus:border-blue-300 outline-none transition-all",
            },
        ),
    )

    song_title = forms.CharField(
        required=False,
        widget=forms.Select(
            choices=[],
            attrs={
                "class": "w-full border border-blue-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-300 focus:border-blue-300 outline-none transition-all",
            },
        ),
    )

    class Meta:
        model = ContentGroup
        fields = [
            "name",
            "start_text",
            "end_text",
            "media_per_video",
            "type",
            "media_per_screen",
            "background",
            "upload_description",
            "song_type",
            "song_title",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Group Name"}
            ),
            "upload_description": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Title for uploaded video",
                }
            ),
            "media_per_video": forms.NumberInput(attrs={"class": "form-control"}),
            "type": forms.Select(attrs={"class": "form-control"}),
            "media_per_screen": forms.Select(attrs={"class": "form-control"}),
            "background": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            initial_type = self.instance.song_type
            self.fields["song_type"].initial = initial_type
            self.fields["song_title"].widget.choices = self.get_song_titles(
                initial_type
            )
            self.fields["song_title"].initial = self.instance.song_title

    def clean_song_title(self):
        # Bypass all validation and return raw value
        return self.cleaned_data.get("song_title")

    def get_song_titles(self, song_type):
        song_titles = [("", "random")]

        if song_type and os.path.exists(os.path.join(AUDIO_PATH, song_type)):
            for file in os.listdir(os.path.join(AUDIO_PATH, song_type)):
                if file.endswith(".mp3"):
                    song_titles.append((file, file[:-4]))

        return song_titles


class SubredditForm(forms.ModelForm):
    types = forms.MultipleChoiceField(
        choices=Subreddit.Type.choices,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "space-y-2"}),
    )

    class Meta:
        model = Subreddit
        fields = ["name", "types"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Add a new subreddit",
                    "class": "border border-gray-300 rounded-l-md px-4 py-2 focus:outline-none focus:ring-blue-500",
                    "required": "required",
                }
            ),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name")

        if re.match(r"^https?://(www\.)?reddit\.com/r/[^/]+", name):
            match = re.search(r"reddit\.com/r/([^/]+)", name)
            if match:
                return match.group(1)
            else:
                raise forms.ValidationError("Please enter a valid Reddit URL.")
        elif re.match(r"^r/", name):
            _, sub_name = name.split("r/")
            return sub_name
        return name

    def clean_types(self):
        types = self.cleaned_data.get("types")

        return ",".join(types)


class FetchPostsForm(forms.Form):
    subreddit = forms.ModelChoiceField(
        queryset=Subreddit.objects.all(),
        widget=Select2Widget(
            attrs={
                "class": "border border-gray-300 rounded-md px-4 py-2",
                "placeholder": "Select a subreddit",
            }
        ),
        required=True,
    )

    time_filter = forms.ChoiceField(
        choices=(
            ("hour", "hour"),
            ("day", "day"),
            ("week", "week"),
            ("month", "month"),
            ("year", "year"),
            ("all", "all"),
        )
    )

    amount = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(
            attrs={
                "class": "border border-gray-300 rounded-md px-4 py-2",
                "placeholder": "Number of posts",
            }
        ),
    )
