from django.urls import path
from . import views

urlpatterns = [
    path('add/kid/', views.AddKidView.as_view(), name='add_kid'),
    path("list/kids/", views.KidsListView.as_view(), name="list_kids"),
    path('change/kid/info/<int:pk>/', views.ChangeKidInfoView.as_view(), name='change_kid_info'),
    path('kid/details/<int:pk>/', views.DetailsKidView.as_view(), name='kid_details'),
    path('kid/search/', views.KidSearchView.as_view(), name='kid-search'),

    path('add/group/', views.GroupAddView.as_view(), name='add_group'),
    path("list/groups/", views.GroupsListView.as_view(), name="list_groups"),
    path('update/group/info/<int:pk>/', views.GroupUpdateView.as_view(), name='group_update'),
    path('group/details/<int:pk>/', views.GroupDetailsView.as_view(), name='group_details'),

    path('add/payments/plans/', views.AddPaymentsPlanView.as_view(), name='add_payment_plans'),
    path('list/payments/plans/', views.PaymentPlansListView.as_view(), name='list_payments_plans'),
    path('update/payments/plans/', views.PaymentPlanUpdateView.as_view(), name='payment_plan_update'),

    path('add/meal/', views.MealAddView.as_view(), name='add_meal'),
    path('list/meals/', views.MealsListView.as_view(), name='list_meals'),
    path('meals/update/<int:pk>/', views.MealsUpdateView.as_view(), name='meals_update'),

]
