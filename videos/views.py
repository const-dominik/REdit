from django.views.generic import FormView
from django.urls import reverse_lazy

from videos.forms import VideoGenerateForm
from videos.scripts.generation import generate_video


class VideoFormView(FormView):
    form_class = VideoGenerateForm
    template_name = "videos/video-form.html"
    success_url = reverse_lazy("dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_name"] = "video-form"

        return context

    def form_valid(self, form):
        generate_video(form.cleaned_data["content_group"])

        return super().form_valid(form)
