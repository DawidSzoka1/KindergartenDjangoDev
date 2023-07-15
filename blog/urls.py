from django.urls import path
from . import views

urlpatterns = [
    path('<int:pk>/', views.CalendarKid.as_view(), name='calendar'),
    path("wydarzenia/", views.PostListView.as_view(), name='post_list_view'),
    path("wydarzenie/szczegoly/<int:pk>/", views.PostDetailView.as_view(), name='post_detail_view'),
    path("wydarzenie/update/<int:pk>/", views.PostUpdateView.as_view(), name='post_update'),
    path("wydarzenie/nowe/", views.PostCreateView.as_view(), name='post_create_view'),
    path("wydarzenie/delete/<int:pk>/", views.PostDeleteView.as_view(), name='post_delete'),
    path("", views.Home.as_view(), name="home_page"),
]
