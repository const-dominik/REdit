from django import forms
from posts.models import ContentGroup, Subreddit

import re


class ContentGroupForm(forms.ModelForm):
    class Meta:
        model = ContentGroup
        fields = [
            "name",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Add a new content group",
                    "class": "border border-gray-300 rounded-l-md px-4 py-2 focus:outline-none focus:ring-blue-500",
                    "required": "required",
                }
            ),
        }


class SubredditForm(forms.ModelForm):
    class Meta:
        model = Subreddit
        fields = ["name"]
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
