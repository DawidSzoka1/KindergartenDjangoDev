from django.urls import path
from . import views

urlpatterns = [

    path('add/group/', views.GroupAddView.as_view(), name='add_group'),
    path("list/groups/", views.GroupsListView.as_view(), name="list_groups"),
    path('update/group/info/<int:pk>/', views.GroupUpdateView.as_view(), name='group_update'),
    path('group/details/<int:pk>/', views.GroupDetailsView.as_view(), name='group_details'),
    path('group/delete/<int:pk>/', views.GroupDeleteView.as_view(), name='group_delete'),

]
