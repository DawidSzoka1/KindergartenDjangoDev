from django.urls import path
from . import views

urlpatterns = [
    path('director/add/teacher/', views.EmployeeAddView.as_view(), name='add_teacher'),
    path('director/list/teachers/', views.EmployeesListView.as_view(), name='list_teachers'),
    path('director/teacher/details/<int:pk>/', views.EmployeeDetailsView.as_view(), name='teacher_details'),
    path('director/teacher/update/<int:pk>/', views.EmployeeUpdateView.as_view(), name='teacher_update'),
    path('director/teacher/search/', views.TeacherSearchView.as_view(), name='teacher-search'),
    path('employee/profile/', views.EmployeeProfileView.as_view(), name='teacher-profile'),
]
