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
        month_name = calendar.month_name[month_number]
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
                   'month_previous': month_previous, 'year_previous': year_previous, 'month_name': month_name,}
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
        presence_type_id = request.POST.get('presence')
        day = request.POST.get('selected_day')

        # Budujemy datę wybraną przez użytkownika
        selected_date = datetime.strptime(f"{year}-{month}-{day}", '%Y-%m-%d').date()
        today = timezone.now().date()

        # BLOKADA: Nie można zmieniać dni wcześniejszych niż dzisiaj
        if selected_date < today:
            messages.error(request, "Nie można zmieniać statusu obecności dla dni przeszłych.")
            return redirect('calendar', pk=pk, month=month, year=year)

        kid = get_object_or_404(Kid, id=int(pk))

        # Ograniczenie dla rodzica - tylko planowana nieobecność (typ 3/2 w zależności od modelu)
        if 'parent.is_parent' in request.user.get_user_permissions():
            if int(presence_type_id) != 3: # Zakładając, że 3 to planowana nieobecność
                messages.error(request, "Rodzic może zgłaszać tylko planowane nieobecności.")
                return redirect('calendar', pk=pk, month=month, year=year)

        PresenceModel.objects.update_or_create(
            day=selected_date,
            kid=kid,
            defaults={'presenceType': int(presence_type_id)}
        )

        messages.success(request, f"Zaktualizowano status dla dnia {day}.")
        return redirect('calendar', pk=pk, month=month, year=year)


from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from datetime import timedelta
from children.models import Kid, PresenceModel
from teacher.models import Employee
from director.models import Director
from parent.models import ParentA

class PresenceCalendarView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        now = timezone.now()
        year, month, day = now.year, now.month, now.day

        # Sprawdzenie czy jest weekend (5=Sobota, 6=Niedziela)
        if now.weekday() >= 5:
            return render(request, 'presence-calendar.html', {'weekend': True})

        user_perms = user.get_user_permissions()

        # Pobieranie dzieci i dyrektora w zależności od roli
        if 'director.is_director' in user_perms:
            director = get_object_or_404(Director, user=user.id)
            kids_qs = director.kid_set.filter(is_active=True)
        elif 'teacher.is_teacher' in user_perms:
            teacher = get_object_or_404(Employee, user=user.id)
            director = teacher.principal.first()
            kids_qs = teacher.group.kid_set.filter(is_active=True)
        elif 'parent.is_parent' in user_perms:
            parent = get_object_or_404(ParentA, user=user.id)
            director = parent.principal.first()
            kids_qs = parent.kids.filter(is_active=True)
        else:
            raise PermissionDenied

        # Filtrowanie wyszukiwania (dla dyrektora)
        search_query = request.POST.get('search')
        if search_query:
            kids_qs = kids_qs.filter(first_name__icontains=search_query)

        kids_qs = kids_qs.order_by('last_name', 'first_name')

        # Paginacja
        paginator = Paginator(kids_qs, 10)
        page_obj = paginator.get_page(request.GET.get('page'))

        # Budowanie słownika obecności (dzisiejszej)
        kids_presence_dict = {}
        today_presences = PresenceModel.objects.filter(day=now.date(), kid__in=page_obj)
        presence_map = {p.kid_id: p for p in today_presences}

        for kid in page_obj:
            kids_presence_dict[kid] = presence_map.get(kid.id)

        tomorrow_date = now.date() + timedelta(days=1)
        tomorrow_weekday = tomorrow_date.weekday()

        context = {
            'page_obj': page_obj,
            'dict': kids_presence_dict,
            'today': now.date(),
            'year': year,
            'month': month,
            'tomorrow': tomorrow_weekday,
            'weekend': False
        }
        return render(request, 'presence-calendar.html', context)

    def post(self, request):
        data_raw = request.POST.get('data')
        if not data_raw:
            return redirect('presence_calendar')

        data = data_raw.split()
        kid_id = int(data[0])
        p_type = int(data[1])

        user_perms = request.user.get_user_permissions()
        kid = get_object_or_404(Kid, id=kid_id, is_active=True)

        # Logika daty: dzisiaj dla personelu, jutro dla rodzica
        if 'parent.is_parent' in user_perms:
            # Sprawdzenie czy dziecko należy do rodzica
            if not kid.parenta_set.filter(user=request.user).exists():
                raise PermissionDenied
            target_date = timezone.now().date() + timedelta(days=1)
        else:
            # Sprawdzenie uprawnień personelu
            target_date = timezone.now().date()
            if 'teacher.is_teacher' in user_perms:
                if kid not in request.user.employee.group.kid_set.all():
                    raise PermissionDenied

        # Zapisywanie obecności
        PresenceModel.objects.update_or_create(
            day=target_date,
            kid=kid,
            defaults={'presenceType': p_type}
        )

        return redirect('presence_calendar')