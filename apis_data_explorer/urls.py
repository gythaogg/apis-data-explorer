from django.urls import include, path
from apis_data_explorer.views import HomeView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
]