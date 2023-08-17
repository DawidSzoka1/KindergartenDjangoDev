from django.urls import path
from . import views

urlpatterns = [
    path('add/kid/', views.AddKidView.as_view(), name='add_kid'),
    path("list/kids/", views.KidsListView.as_view(), name="list_kids"),
    path('change/kid/info/<int:pk>/', views.ChangeKidInfoView.as_view(), name='change_kid_info'),
    path('kid/details/<int:pk>/', views.DetailsKidView.as_view(), name='kid_details'),
    path('kid/delete/<int:pk>/', views.KidDeleteView.as_view(), name='kid_delete'),

    path('add/payments/plans/', views.AddPaymentsPlanView.as_view(), name='add_payment_plans'),
    path('list/payments/plans/', views.PaymentPlansListView.as_view(), name='list_payments_plans'),
    path('update/payments/plans/<int:pk>/', views.PaymentPlanUpdateView.as_view(), name='payment_plan_update'),
    path('delete/payments/plans/<int:pk>/', views.PaymentPlanDeleteView.as_view(), name='payment_plan_delete'),

    path('add/meal/', views.MealAddView.as_view(), name='add_meal'),
    path('list/meals/', views.MealsListView.as_view(), name='list_meals'),
    path('meals/update/<int:pk>/', views.MealsUpdateView.as_view(), name='meals_update'),
    path('meals/delete/<int:pk>/', views.MealDeleteView.as_view(), name='meals_delete'),

]
