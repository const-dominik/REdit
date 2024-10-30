from django.views.generic import ListView
from posts.models import Subreddit, ContentGroup
from posts.forms import SubredditForm, ContentGroupForm
from django.shortcuts import render, redirect
from posts.serializers import SubredditSerializer, ContentGroupSerializer
from rest_framework import viewsets
from django.http import JsonResponse
import json


class SubredditList(ListView):
    model = Subreddit
    template_name = "posts/subreddits.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_name"] = "subreddits"
        context["form"] = SubredditForm

        return context

    def post(self, request, *args, **kwargs):
        subreddit_form = SubredditForm(request.POST)

        if subreddit_form.is_valid():
            subreddit_form.save()

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
            subreddit_id = data["subreddit_id"]
            try:
                subreddit = Subreddit.objects.get(id=subreddit_id)
                group = ContentGroup.objects.get(id=group_id)
                if group.subreddits.filter(id=subreddit_id).exists():
                    group.subreddits.remove(subreddit)
                else:
                    group.subreddits.add(subreddit)
                return JsonResponse({"success": True})
            except (Subreddit.DoesNotExist, ContentGroup.DoesNotExist):
                return JsonResponse(
                    {"success": False, "error": "Subreddit or Content Group not found."}
                )

        return redirect("contentgroups")


class ContentGroupViewSet(viewsets.ModelViewSet):
    queryset = ContentGroup.objects.all()
    serializer_class = ContentGroupSerializer
