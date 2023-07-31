from django.urls import path
from . import views

urlpatterns = [
    path('profile/password/update/', views.ProfilePasswordUpdate.as_view(), name='password_change'),
    path('register/', views.Register.as_view(), name='register'),
]
