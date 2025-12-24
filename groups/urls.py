from django.urls import path
from . import views

urlpatterns = [

    path('add/group/', views.GroupAddView.as_view(), name='add_group'),
    path("list/groups/", views.GroupsListView.as_view(), name="list_groups"),
    path('update/group/info/<int:pk>/', views.GroupUpdateView.as_view(), name='group_update'),
    path('group/details/<int:pk>/', views.GroupDetailsView.as_view(), name='group_details'),
    path('group/delete/<int:pk>/', views.GroupDeleteView.as_view(), name='group_delete'),
    path('group/<int:pk>/assign-kid/', views.AssignExistingKidToGroupView.as_view(), name='assign_kid_to_group'),
    path('group/<int:pk>/assign-teachers/', views.AssignTeachersView.as_view(), name='assign_teachers'),
    path('kid/<int:kid_pk>/remove-from-group/', views.RemoveKidFromGroupView.as_view(), name='remove_kid_from_group'),
    path('teacher/<int:teacher_pk>/remove-from-group/', views.RemoveTeacherFromGroupView.as_view(), name='remove_teacher_from_group'),
]
