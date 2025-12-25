from django.urls import path
from . import views

urlpatterns = [
    path('add/payments/plans/', views.AddPaymentsPlanView.as_view(), name='add_payment_plans'),
    path('list/payments/plans/', views.PaymentPlansListView.as_view(), name='list_payments_plans'),
    path('update/payments/plans/<int:pk>/', views.PaymentPlanUpdateView.as_view(), name='payment_plan_update'),
    path('delete/payments/plans/<int:pk>/', views.PaymentPlanDeleteView.as_view(), name='payment_plan_delete'),
    path('details/payments/plans/<int:pk>/', views.PaymentPlanDetailsView.as_view(), name='payment_plan_details'),
    path('moje-platnosci/', views.ParentPaymentsView.as_view(), name='parent_payments'),
    path('podsumowanie-finansowe/', views.DirectorFinanceSummaryView.as_view(), name='director_finance'),

]
