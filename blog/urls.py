from django.urls import path
from . import views

urlpatterns = [
    path("wydarzenia/", views.PostListView.as_view(), name='post_list_view'),
    path("wydarzenia/wyszukane/", views.PostSearchView.as_view(), name='post_search'),
    path("wydarzenia/zmień/<int:pk>/", views.PostUpdateView.as_view(), name='post_update'),
    path("", views.Home.as_view(), name="home_page"),
]
