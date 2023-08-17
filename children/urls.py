from django.urls import path
from . import views

urlpatterns = [
    path('add/kid/', views.AddKidView.as_view(), name='add_kid'),
    path("list/kids/", views.KidsListView.as_view(), name="list_kids"),
    path('change/kid/info/<int:pk>/', views.ChangeKidInfoView.as_view(), name='change_kid_info'),
    path('kid/details/<int:pk>/', views.DetailsKidView.as_view(), name='kid_details'),
    path('kid/delete/<int:pk>/', views.KidDeleteView.as_view(), name='kid_delete'),
    path('kid/parent/info/<int:pk>/', views.KidParentInfoView.as_view(), name='kid_parent'),

]
