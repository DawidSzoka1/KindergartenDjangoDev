from django.urls import path
from . import views

urlpatterns = [
    path('director/add/teacher/', views.AddTeacherView.as_view(), name='add_teacher'),
    path('director/list/teachers/', views.TeachersListView.as_view(), name='list_teachers'),
    path('director/teacher/details/<int:pk>/', views.TeacherDetailsView.as_view(), name='teacher_details'),
    path('director/teacher/update/<int:pk>/', views.TeacherUpdateView.as_view(), name='teacher_update'),
    path('director/teacher/search/', views.TeacherSearchView.as_view(), name='teacher-search'),
]
