from django.urls import path
from . import views

urlpatterns = [
    path("director/profile/", views.DirectorProfileView.as_view(), name="director_profile"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path("contact/update/", views.ContactUpdateView.as_view(), name="contact-update"),

]
