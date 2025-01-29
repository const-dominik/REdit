from django.views.generic import TemplateView
from dashboard.scripts import get_stats_analytics, get_shorts_analytics

from videos.models import UploadedVideo


# Create your views here.
class Dashboard(TemplateView):
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_name"] = "dashboard"
        context["yt_shorts"] = get_stats_analytics()
        video_ids = UploadedVideo.objects.filter(platform="Youtube").values_list(
            "uploaded_video_id", flat=True
        )
        print(get_shorts_analytics(list(video_ids)))

        return context
