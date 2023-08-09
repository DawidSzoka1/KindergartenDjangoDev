from django.urls import path
from . import views

urlpatterns = [
    path('add/kid/', views.AddKidView.as_view(), name='add_kid'),
    path('add/group/', views.AddGroupView.as_view(), name='add_group'),
    path('add/payments/plans/', views.AddPaymentsPlanView.as_view(), name='add_payment_plans'),
    path('add/meal/', views.AddMealView.as_view(), name='add_meal'),
    path("list/kids/", views.KidsListView.as_view(), name="list_kids"),
    path("list/groups", views.GroupsListView.as_view(), name="list_groups"),
    path('list/payments/plans/', views.PaymentPlansListView.as_view(), name='list_payments_plans'),
    path('list/meals/', views.MealsListView.as_view(), name='list_meals'),
    path('change/kid/info/<int:pk>/', views.ChangeKidInfoView.as_view(), name='change_kid_info'),
    path('kid/details/<int:pk>/', views.DetailsKidView.as_view(), name='kid_details'),
    path('group/details/<int:pk>/', views.GroupDetailsView.as_view(), name='group_details'),
    path('kid/search/', views.KidSearchView.as_view(), name='kid-search'),


]
