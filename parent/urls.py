from django.urls import path
from . import views

urlpatterns = [
    path('parent/profile/<int:pk>/', views.ParentProfileView.as_view(), name='parent_profile'),
    path('list/parents/', views.ParentListView.as_view(), name='list_parent'),
    path('invite/parent/<int:pk>/', views.InviteParentView.as_view(), name='invite_parent'),
    path('parent/delete/<int:pk>/', views.ParentDeleteView.as_view(), name='parent_delete'),
    path('parent/search/', views.ParentSearchView.as_view(), name='parent-search'),
]
