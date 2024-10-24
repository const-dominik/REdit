from django.views.generic import ListView
from posts.models import Subreddit, ContentGroup
from posts.forms import SubredditForm, ContentGroupForm
from django.shortcuts import render, redirect


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


class ContentGroupList(ListView):
    model = ContentGroup
    template_name = "posts/groups.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_name"] = "groups"
        context["form"] = ContentGroupForm

        return context

    def post(self, request, *args, **kwargs):
        content_groups_form = ContentGroupForm(request.POST)

        if content_groups_form.is_valid():
            content_groups_form.save()

        return redirect("contentgroups")
