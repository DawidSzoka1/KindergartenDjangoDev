from django.urls import path
from . import views

urlpatterns = [
    path('calendar/<int:pk>/<int:month>/<int:year>/', views.CalendarKid.as_view(), name='calendar'),
    path('presence/calendar/', views.PresenceCalendarView.as_view(), name='presence_calendar'),
    path("wydarzenia/", views.PostListView.as_view(), name='post_list_view'),
    path("wydarzenia/wyszukane/", views.PostSearchView.as_view(), name='post_search'),
    path("", views.Home.as_view(), name="home_page"),
]
