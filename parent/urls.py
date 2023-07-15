from django.urls import path
from . import views

urlpatterns = [
    path('parent/profile/', views.ParentProfileView.as_view(), name='parent_profile'),
]
