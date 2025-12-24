import calendar
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from parent.models import ParentA
from teacher.models import Employee
from director.models import FreeDaysModel, Director
from children.models import PresenceModel, Kid, presenceChoices
from django.utils.safestring import mark_safe
from django.contrib import messages
from datetime import datetime, timedelta
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from calendar import HTMLCalendar


class Calendar(HTMLCalendar):
    def __init__(self, year=None, month=None, director=None, kid=None):
        self.year = year
        self.month = month
        self.director = director
        self.kid = kid
        super(Calendar, self).__init__()

    def formatday(self, day, events):
        if day == 0:
            return '<div class="h-12 w-full"></div>' # Puste miejsce

        # Logika sprawdzania czy to weekend
        is_weekend = calendar.weekday(self.year, self.month, day) in [5, 6]

        # Pobieranie obecności dla tego dnia
        presence = PresenceModel.objects.filter(kid=self.kid, day__year=self.year, day__month=self.month, day__day=day).first()

        # Sprawdzanie czy to dzisiaj
        is_today = (timezone.now().year == self.year and timezone.now().month == self.month and timezone.now().day == day)

        # Klasy bazowe
        css_classes = "h-12 w-full text-sm font-medium rounded-xl transition-all flex items-center justify-center relative "

        if is_today:
            css_classes += "bg-primary text-white shadow-lg shadow-primary/30 z-10 "
        elif is_weekend:
            css_classes += "text-gray-300 dark:text-gray-700 cursor-not-allowed "
        else:
            css_classes += "text-gray-700 dark:text-gray-300 hover:bg-primary/10 "

        # Nakładanie statusów kolorystycznych
        status_dot = ""
        if presence:
            if presence.presenceType == 1: # Nieobecność
                css_classes += "bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 "
                status_dot = '<span class="absolute bottom-1 size-1 bg-red-500 rounded-full"></span>'
            elif presence.presenceType == 2: # Obecność
                css_classes += "bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 "
                status_dot = '<span class="absolute bottom-1 size-1 bg-green-500 rounded-full"></span>'
            elif presence.presenceType == 3: # Planowana
                css_classes += "bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 "
                status_dot = '<span class="absolute bottom-1 size-1 bg-blue-500 rounded-full"></span>'

        return f'<button type="button" id="days" class="{css_classes}"><span class="day-num">{day}</span>{status_dot}</button>'

    def formatweek(self, theweek, events):
        week = ''
        for d, weekday in theweek:
            week += self.formatday(d, events)
        return f'<div class="grid grid-cols-7 gap-2">{week}</div>'

    def formatmonth(self, withyear=True):
        events = FreeDaysModel.objects.filter(principal=self.director, start_time__year=self.year, start_time__month=self.month)

        body = ""
        for week in self.monthdays2calendar(self.year, self.month):
            body += self.formatweek(week, events)

        return body


class CalendarKid(LoginRequiredMixin, View):
    def get(self, request, pk, month, year):
        permissions = request.user.get_user_permissions()
        kid = get_object_or_404(Kid, id=int(pk))
        month_number = int(month)
        year_number = int(year)
        day_current = int(timezone.now().day)
        month_next = month_number + 1
        year_previous = year_number
        year_next = year_number
        month_previous = month_number - 1
        if month_number == 12:
            month_next = 1
            year_next = year_number + 1
        elif month_number == 1:
            year_previous = year_number - 1
            month_previous = 12
        cal = Calendar(year=year_number, month=month_number, kid=kid).formatmonth(
            withyear=True)
        context = {'cal': mark_safe(cal), 'day_current': day_current, 'kid': kid, 'month': month_number,
                   'year': year, 'month_next': month_next, 'year_next': year_next,
                   'month_previous': month_previous, 'year_previous': year_previous}
        if not kid.is_active:
            raise PermissionDenied
        elif permissions == {'director.is_director'}:
            director = get_object_or_404(Director, user=request.user.id)
            if kid.principal == director:
                return render(request, 'calendar.html',
                              context=context)
        elif permissions == {'teacher.is_teacher'}:
            teacher = get_object_or_404(Employee, user=request.user.id)
            kids = list(teacher.group.kid_set.filter(is_active=True))
            if kid in kids:
                return render(request, 'calendar.html',
                              context=context)
        elif permissions == {'parent.is_parent'}:
            parent = get_object_or_404(ParentA, user=request.user.id)
            parent_kids = list(parent.kids.filter(is_active=True))
            if kid in parent_kids:
                return render(request, 'calendar.html',
                              context=context)
            raise PermissionDenied

    def post(self, request, pk, month, year):
        # Pobieramy dane wysłane z nowego formularza
        presence_type_id = request.POST.get('presence') # np. "1", "2" lub "3"
        day = request.POST.get('selected_day') # pobrane z pola hidden

        if not day or not presence_type_id:
            messages.error(request, "Nie wybrano dnia lub statusu.")
            return redirect('calendar', pk=pk, month=month, year=year)

        # Tworzymy pełną datę na podstawie parametrów URL i wybranego dnia
        try:
            date_str = f"{year}-{month}-{day}"
            presence_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Nieprawidłowa data.")
            return redirect('calendar', pk=pk, month=month, year=year)

        kid = get_object_or_404(Kid, id=int(pk))

        # Aktualizacja lub stworzenie rekordu obecności
        presence_record, created = PresenceModel.objects.update_or_create(
            day=presence_date,
            kid=kid,
            defaults={'presenceType': int(presence_type_id)}
        )

        messages.success(request, f"Zmieniono status obecności dla {kid.first_name}.")
        return redirect('calendar', pk=pk, month=month, year=year)


class PresenceCalendarView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        month = int(timezone.now().month)
        year = int(timezone.now().year)
        day = int(timezone.now().day)
        if calendar.weekday(year=year, month=month, day=day) == 5 or calendar.weekday(year=year,
                                                                                      month=month,
                                                                                      day=day) == 6:
            return render(request, 'presence-calendar.html',
                          {'weekend': True})
        elif user.get_user_permissions() == {'director.is_director'}:
            director = get_object_or_404(Director, user=user.id)
            kids = director.kid_set.filter(is_active=True).order_by('-id')

        elif user.get_user_permissions() == {'teacher.is_teacher'}:
            teacher = get_object_or_404(Employee, user=user.id)
            director = teacher.principal.first()
            kids = teacher.group.kid_set.filter(is_active=True).order_by('-id')
        elif user.get_user_permissions() == {'parent.is_parent'}:
            parent = get_object_or_404(ParentA, user=user.id)
            director = parent.principal.first()
            kids = parent.kids.filter(is_active=True).order_by('-id')
        else:
            raise PermissionDenied
        kids_presence = PresenceModel.objects.filter(day=timezone.now()).filter(kid__principal=director).filter(
            presenceType=2)
        kids_absent = PresenceModel.objects.filter(day=timezone.now()).filter(kid__principal=director).filter(
            presenceType=1)
        kids_planned_absent = PresenceModel.objects.filter(day=timezone.now()).filter(
            kid__principal=director).filter(
            presenceType=3)
        today = timezone.now().strftime("%Y-%m-%d")
        dict = {}
        for kid in kids:
            presence = PresenceModel.objects.filter(kid=kid).filter(day=timezone.now()).first()
            dict[kid] = presence

        paginator = Paginator(kids, 10)
        page = request.GET.get('page')
        page_obj = paginator.get_page(page)
        tomorrow = (timezone.now() + timedelta(days=1)).weekday()
        return render(request, 'presence-calendar.html',
                      {'page_obj': page_obj,
                       'today': today,
                       'kids_presence': kids_presence,
                       'kids_absent': kids_absent,
                       'kids_planned_absent': kids_planned_absent,
                       'dict': dict,
                       'year': year,
                       'month': month,
                       'tomorrow': tomorrow
                       })

    def post(self, request):
        data = request.POST.get('data')
        data = data.split()
        user = request.user.get_user_permissions()
        kid_id = data[0]
        type = data[1]
        day = timezone.now().strftime("%Y-%m-%d")
        kid = Kid.objects.filter(id=int(kid_id)).filter(is_active=True).first()
        check = PresenceModel.objects.filter(kid=kid).filter(day=day).first()
        if user == {'parent.is_parent'}:
            if kid:
                if request.user.email in kid.parenta_set.values_list('user__email', flat=True):
                    day = (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                    check = PresenceModel.objects.filter(kid=kid).filter(day=day).first()
                    if check:
                        check.presenceType = int(type)
                        check.save()
                    else:
                        PresenceModel.objects.create(day=day, kid=kid, presenceType=int(type))
        elif user == {'director.is_director'}:
            director = Director.objects.get(user=request.user.id)
            if kid:
                if kid.id in director.kid_set.filter(is_active=True).values_list('id', flat=True):
                    if check:
                        check.presenceType = int(type)
                        check.save()
                    else:
                        PresenceModel.objects.create(day=day, kid=kid, presenceType=int(type))
        elif user == {'teacher.is_teacher'}:
            if kid in request.user.employee.group.kid_set.filter(is_active=True):
                if check:
                    check.presenceType = int(type)
                    check.save()
                else:
                    PresenceModel.objects.create(day=day, kid=kid, presenceType=int(type))

        return redirect('presence_calendar')
