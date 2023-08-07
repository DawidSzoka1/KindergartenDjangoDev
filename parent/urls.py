from django.urls import path
from . import views

urlpatterns = [
    path('parent/profile/', views.ParentProfileView.as_view(), name='parent_profile'),
    path('director/list/parents/', views.ParentListView.as_view(), name='list_parent'),
    path('director/invite/parent/<int:pk>/', views.InviteParentView.as_view(), name='invite_parent'),
    path('director/parent/details/<int:pk>/', views.DetailsParentView.as_view(), name='parent_details'),
]
