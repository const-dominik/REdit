from django import forms
from posts.models import ContentGroup
from django_select2.forms import Select2Widget


class VideoGenerateForm(forms.Form):
    content_group = forms.ModelChoiceField(
        queryset=ContentGroup.objects.all(),
        widget=Select2Widget(
            attrs={
                "class": "border border-gray-300 rounded-md px-4 py-2",
            }
        ),
        required=True,
    )

    # and whatever we end up needing while generating video
