from django.urls import path
from  apis_data_explorer.views import HomeView,EntitySearchView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("search/", EntitySearchView.as_view(), name="search"),

]
