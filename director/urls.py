from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path("director/profile/", views.DirectorProfileView.as_view(), name="director_profile"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path("contact/update/<int:pk>/", views.ContactUpdateView.as_view(), name="contact-update"),
    path("photos/list/", views.PhotosListView.as_view(), name="photos_list"),
    path("photo/add/", views.PhotosAddView.as_view(), name="photo_add"),
    path("photo/delete/<int:pk>/", views.PhotoDeleteView.as_view(), name="photo_delete"),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
