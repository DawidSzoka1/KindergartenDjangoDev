from django.urls import path
from . import views

urlpatterns = [
    path("director/profile/", views.DirectorProfileView.as_view(), name="director_profile"),
    path('director/add/kid/', views.AddKidView.as_view(), name='add_kid'),
    path('director/add/group/', views.AddGroupView.as_view(), name='add_group'),
    path('director/add/payments/plans/', views.AddPaymentsPlanView.as_view(), name='add_payment_plans'),
    path('director/add/meal/', views.AddMealView.as_view(), name='add_meal'),
    path('director/add/teacher/', views.AddTeacherView.as_view(), name='add_teacher'),

    path("director/list/kids/", views.KidsListView.as_view(), name="list_kids"),
    path("director/list/groups", views.GroupsListView.as_view(), name="list_groups"),
    path('director/list/payments/plans/', views.PaymentPlansListView.as_view(), name='list_payments_plans'),
    path('director/list/meals/', views.MealsListView.as_view(), name='list_meals'),
    path('director/list/teachers/', views.TeachersListView.as_view(), name='list_teachers'),

    path('director/change/kid/info/<int:pk>/', views.ChangeKidInfoView.as_view(), name='change_kid_info'),
    path('director/invite/parent/<int:pk>/', views.InviteParentView.as_view(), name='invite_parent'),
    path('director/kid/details/<int:pk>/', views.DetailsKidView.as_view(), name='kid_details'),
    path('director/parent/details/<int:pk>/', views.DetailsParentView.as_view(), name='parent_details'),

]
