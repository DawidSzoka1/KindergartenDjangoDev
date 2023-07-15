from django.urls import path
from . import views

urlpatterns = [
    path('addKid/', views.AddKid.as_view(), name='addKid'),
    path("settings/", views.DirectorProfile.as_view(), name="director_profile"),
    path("kids/", views.Kids.as_view(), name="kids"),
    path("groups/", views.GroupsView.as_view(), name="groups"),
    path('addGroup/', views.AddGroup.as_view(), name='addGroup'),
    path('paymentsPlans/', views.PaymentPlans.as_view(), name='payments_plans'),
    path('add/payments/plans/', views.AddPaymentsPlan.as_view(), name='add_payment_plans'),
    path('change/info/', views.ChangeInfo.as_view(), name='change_info'),
    path('invite/parent/', views.InviteParent.as_view(), name='invite_parent'),
    path('add/meal/', views.AddMeals.as_view(), name='add_meals'),
    path('all/meals/', views.AllMeals.as_view(), name='all_meals'),
    path('kid/details/', views.DetailsKid.as_view(), name='kid_details'),
]
