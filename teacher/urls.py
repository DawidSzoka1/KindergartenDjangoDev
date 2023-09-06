from django.urls import path
from . import views

urlpatterns = [
    path('add/teacher/', views.EmployeeAddView.as_view(), name='add_teacher'),
    path('list/teachers/', views.EmployeesListView.as_view(), name='list_teachers'),
    path('teacher/update/<int:pk>/', views.EmployeeUpdateView.as_view(), name='teacher_update'),
    path('employee/profile/<int:pk>/', views.EmployeeProfileView.as_view(), name='teacher-profile'),
    path('employee/delete/<int:pk>/', views.EmployeeDeleteView.as_view(), name='teacher_delete'),
]
