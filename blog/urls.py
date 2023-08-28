from django.urls import path
from . import views

urlpatterns = [
    path("wydarzenia/", views.PostListView.as_view(), name='post_list_view'),
    path("wydarzenia/wyszukane/", views.PostSearchView.as_view(), name='post_search'),
    path("", views.Home.as_view(), name="home_page"),
]
