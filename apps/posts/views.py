import json
import os

from django.views.generic import ListView, FormView
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.conf import settings

from apps.posts.models import Subreddit, ContentGroup
from apps.posts.forms import SubredditForm, ContentGroupForm, FetchPostsForm
from apps.posts.serializers import SubredditSerializer, ContentGroupSerializer
from apps.posts.scripts import fetch_posts
from rest_framework import viewsets


class SubredditList(ListView):
    model = Subreddit
    template_name = "posts/subreddits.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_name"] = "subreddits"
        context["form"] = SubredditForm
        content_types = {
            "img": "🖼️",
            "vid": "🎥",
            "text": "📝",
        }

        context["content_types"] = content_types
        return context

    def post(self, request, *args, **kwargs):
        if request.POST:
            subreddit_form = SubredditForm(request.POST)

            if subreddit_form.is_valid():
                subreddit_form.save()

        elif request.body:
            data = json.loads(request.body)

            subreddit_id = data["subreddit_id"]
            type = data["type"]

            try:
                subreddit = Subreddit.objects.get(id=subreddit_id)
                removed = subreddit.toggle_type(type)
                subreddit.save()
                return JsonResponse({"success": True, "removed": removed})
            except Subreddit.DoesNotExist:
                pass

        return redirect("subreddits")


class SubredditViewSet(viewsets.ModelViewSet):
    queryset = Subreddit.objects.all()
    serializer_class = SubredditSerializer


class ContentGroupList(ListView):
    model = ContentGroup
    template_name = "posts/groups.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_name"] = "groups"
        context["subreddits_available"] = Subreddit.objects.all()
        context["new_group_form"] = ContentGroupForm()

        context["group_forms"] = {
            group.id: ContentGroupForm(instance=group)
            for group in context["object_list"]
        }
        return context

    def post(self, request, *args, **kwargs):
        if request.POST:
            form = ContentGroupForm(request.POST)
            if "name" in form.data:
                ContentGroup.objects.create(name=form.data["name"])
                return HttpResponseRedirect(reverse_lazy("contentgroups"))
            else:
                return JsonResponse({"success": False, "errors": form.errors})

        elif request.body:
            data = json.loads(request.body)
            group_id = data.get("group_id")

            group = get_object_or_404(ContentGroup, id=group_id)

            if "subreddit_id" in data:
                subreddit = Subreddit.objects.get(id=data["subreddit_id"])
                if group.subreddits.filter(id=data["subreddit_id"]).exists():
                    group.subreddits.remove(subreddit)
                else:
                    group.subreddits.add(subreddit)
                group.save()
                return JsonResponse({"success": True})

            form = ContentGroupForm(data, instance=group)
            if form.is_valid():
                form.save()
                return JsonResponse({"success": True})
            else:
                return JsonResponse({"success": False, "errors": form.errors})


class ContentGroupViewSet(viewsets.ModelViewSet):
    queryset = ContentGroup.objects.all()
    serializer_class = ContentGroupSerializer


class PostsFormView(FormView):
    form_class = FetchPostsForm
    template_name = "posts/posts-form.html"
    success_url = reverse_lazy("posts-fetch")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_name"] = "posts-fetch"

        return context

    def form_valid(self, form):
        fetch_posts(**form.cleaned_data)

        return super().form_valid(form)


AUDIO_PATH = settings.STATIC_ROOT + "/video_assets/audios/"


def get_song_titles(request):
    song_type = json.loads(request.body)["song_type"]
    song_titles = [("random", "")]

    if song_type and os.path.exists(os.path.join(AUDIO_PATH, song_type)):
        for file in os.listdir(os.path.join(AUDIO_PATH, song_type)):
            if file.endswith(".mp3"):
                song_name = file.split(".mp3")[0]
                song_titles.append((song_name, file))

    return JsonResponse({"results": song_titles})
