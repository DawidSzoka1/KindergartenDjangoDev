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

    # formats a day as a td
    # filter events by day
    def formatday(self, day, events):
        events_per_day = events.filter(start_time__day=day)
        d = ''
        for event in events_per_day:
            d += f'<li> {event.title} </li>'

        presences = PresenceModel.objects.filter(kid=self.kid)

        if day != 0:
            if calendar.weekday(year=self.year, month=self.month, day=day) == 5 or calendar.weekday(year=self.year,
                                                                                                    month=self.month,
                                                                                                    day=day) == 6:
                return f"<td id='freeday' style='color: #E6DCD3'><span class='date'>{day}</span></td>"
            for presence in presences:

                if day == presence.day.day and self.month == presence.day.month and self.year == presence.day.year:
                    if presence.presenceType == 1:
                        return f"<td id='days' style='background-color: #FF5F57'><span class='date'>{day}</span></td>"
                    elif presence.presenceType == 2:
                        return f"<td id='days' style='background-color: #A5FE90'><span class='date'>{day}</span></td>"
                    elif presence.presenceType == 3:
                        return f"<td id='days' style='background-color: #B4F3F5'><span class='date table-info'>{day}</span></td>"
            return f"<td id='days'><span class='date'>{day}</span></td>"
        return f'<td></td>'

    # formats a week as a tr
    def formatweek(self, theweek, events):
        week = ''
        for d, weekday in theweek:
            week += self.formatday(d, events)
        return f"<tr class='test'> {week} </tr>"

    # formats a month as a table
    # filter events by year and month
    def formatmonth(self, withyear=True):
        events = FreeDaysModel.objects.filter(principal=self.director).filter(start_time__year=self.year,
                                                                              start_time__month=self.month)

        cal = f'<table border="0" cellpadding="21" cellspacing="21" align="center" class="calendar">\n'
        cal += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
        cal += f'{self.formatweekheader()}\n'
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f'{self.formatweek(week, events)}\n'
        return cal


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
        presence = request.POST.get('presence')
        presence = presence.split(' ')
        presence_type = presence.pop(-1)
        month_name = presence[1]
        month_number = datetime.strptime(month_name, '%B').month
        presence[1] = f'{month_number}'
        presence.reverse()
        presence = '-'.join(presence)
        presence_type = presenceChoices[int(presence_type)][0]
        kid = get_object_or_404(Kid, id=int(pk))
        test = PresenceModel.objects.filter(kid=kid).filter(day=presence).first()
        if test:
            test.presenceType = presence_type
            test.save()
        else:
            PresenceModel.objects.create(day=presence, kid=kid, presenceType=presence_type)
        messages.success(request, f"Zmieniono obecnosc")
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
