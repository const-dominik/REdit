from django import forms
from posts.models import ContentGroup, Subreddit
from django_select2.forms import Select2Widget

import re


class ContentGroupForm(forms.ModelForm):
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
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Group Name"}
            ),
            "start_text": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Start Text"}
            ),
            "end_text": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "End Text"}
            ),
            "media_per_video": forms.NumberInput(attrs={"class": "form-control"}),
            "type": forms.Select(attrs={"class": "form-control"}),
            "media_per_screen": forms.Select(attrs={"class": "form-control"}),
            "background": forms.Select(attrs={"class": "form-control"}),
        }


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
