from django.urls import path
from . import views

urlpatterns = [

    path('add/meal/', views.MealAddView.as_view(), name='add_meal'),
    path('list/meals/', views.MealsListView.as_view(), name='list_meals'),
    path('meals/update/<int:pk>/', views.MealsUpdateView.as_view(), name='meals_update'),
    path('meals/delete/<int:pk>/', views.MealDeleteView.as_view(), name='meals_delete'),
    path('meals/details/<int:pk>/', views.MealDetailsView.as_view(), name='meal_details'),

]
