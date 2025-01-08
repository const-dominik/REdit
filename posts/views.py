from django.views.generic import ListView, FormView
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.urls import reverse_lazy

import json
from posts.models import Subreddit, ContentGroup, Post
from posts.forms import SubredditForm, ContentGroupForm, FetchPostsForm
from posts.serializers import SubredditSerializer, ContentGroupSerializer
from posts.scripts import fetch_posts
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

        if request.body:
            data = json.loads(request.body)

            subreddit_id = data["subreddit_id"]
            type = data["type"]

            try:
                subreddit = Subreddit.objects.get(id=subreddit_id)
                removed = subreddit.toggle_type(type)
                subreddit.save()
                return JsonResponse({"success": True, "removed": removed})
            except Subreddit.DoesNotExist:
                print("xd")

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
        context["form"] = ContentGroupForm

        return context

    def post(self, request, *args, **kwargs):
        if request.POST:
            content_groups_form = ContentGroupForm(request.POST)
            if content_groups_form.is_valid():
                content_groups_form.save()

        elif request.body:
            data = json.loads(request.body)
            group_id = data["group_id"]

            try:
                group = ContentGroup.objects.get(id=group_id)

                if "new_name" in data:
                    group.name = data["new_name"]

                if "theme" in data:
                    group.theme = data["theme"]

                if "subreddit_id" in data:
                    subreddit = Subreddit.objects.get(id=data["subreddit_id"])
                    if group.subreddits.filter(id=data["subreddit_id"]).exists():
                        group.subreddits.remove(subreddit)
                    else:
                        group.subreddits.add(subreddit)

                group.save()

                return JsonResponse({"success": True})

            except (ContentGroup.DoesNotExist, Subreddit.DoesNotExist):
                return JsonResponse(
                    {"success": False, "error": "Subreddit or Content Group not found."}
                )

        return redirect("contentgroups")


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


class PostsView(ListView):
    model = Post
    template_name = "posts/posts.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_name"] = "posts"
        return context
