from django.views.generic import TemplateView

class HomeView(TemplateView):
    template_name = "apis_data_explorer/home.html"
