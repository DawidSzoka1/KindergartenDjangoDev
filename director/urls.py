from django.urls import path
from . import views

urlpatterns = [
    path("director/profile/", views.DirectorProfileView.as_view(), name="director_profile"),
]
