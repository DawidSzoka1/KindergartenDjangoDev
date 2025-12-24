from django.urls import path
from . import views

urlpatterns = [
    path('parent/profile/<int:pk>/', views.ParentProfileView.as_view(), name='parent_profile'),
    path('list/parents/', views.ParentListView.as_view(), name='list_parent'),
    path('invite/parent/<int:pk>/', views.InviteParentView.as_view(), name='invite_parent'),
    path('parent/delete/<int:pk>/', views.ParentDeleteView.as_view(), name='parent_delete'),
    path('parent/update/<int:pk>/', views.ParentUpdateView.as_view(), name='parent_update'),
    path('parent/kid/add/<int:pk>/', views.AddParentToKidView.as_view(), name='add_parent_to_kid'),
    path('create-parent-ajax/', views.create_parent_ajax, name='create_parent_ajax'),
    path('parent/search/', views.ParentSearchView.as_view(), name='parent-search'),
    path('invite/parent/', views.InviteAndAssignParentView.as_view(), name='invite_standalone_parent'),
    path('parent/<int:parent_pk>/remove-kid/<int:kid_pk>/', views.RemoveKidFromParentView.as_view(), name='remove_kid_from_parent'),
]
