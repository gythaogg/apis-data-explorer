from django.urls import path
from  apis_data_explorer.views import HomeView,EntitySearchView

urlpatterns = [
    path("", EntitySearchView.as_view(), name="explore"),
]
