from django.urls import path
from . import views

urlpatterns = [
    path('calendar/<int:pk>/<int:month>/<int:year>/', views.CalendarKid.as_view(), name='calendar'),
    path('presence/calendar/', views.PresenceCalendarView.as_view(), name='presence_calendar'),

]
