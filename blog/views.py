from django.shortcuts import render, HttpResponse, redirect
from django.views import View
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin, LoginRequiredMixin
from .models import Post
from director.models import FreeDaysModel
from children.models import PresenceModel, Kid, presenceChoices
from django.contrib.auth.models import Permission
from django.utils.safestring import mark_safe
from django.contrib import messages

from datetime import datetime
import calendar
from django.utils import timezone
from calendar import HTMLCalendar
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)


# class Calendar(HTMLCalendar):
#     def __init__(self, year=None, month=None, kid=None):
#         self.year = year
#         self.month = month
#         self.kid = kid
#         super(Calendar, self).__init__()
#
#     # formats a day as a td
#     # filter events by day
#     def formatday(self, day, events):
#         presences = PresenceModel.objects.filter(kid=self.kid)
#         if day != 0:
#             for presence in presences:
#                 if presence.presenceType == 1:
#                     return f"<td><span class='date table-danger'>{day}</span></td>"
#                 elif presence.presenceType == 2:
#                     return f"<td><span class='date table-success'>{day}</span></td>"
#                 elif presence.presenceType == 3:
#                     return f"<td><span class='date table-info'>{day}</span></td>"
#         return f"<td><span class='date table-dark'>{day}</span></td>"


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

            for presence in presences:
                if day == presence.day.day:
                    if presence.presenceType == 1:
                        return f"<td id='days' style='background-color: red'><span class='date'>{day}</span></td>"
                    elif presence.presenceType == 2:
                        return f"<td id='days' style='background-color: green'><span class='date'>{day}</span></td>"
                    elif presence.presenceType == 3:
                        return f"<td id='days' style='background-color: grey'><span class='date table-info'>{day}</span></td>"
            return f"<td id='days'><span class='date'>{day}</span></td>"
        return '<td></td>'

    # formats a week as a tr
    def formatweek(self, theweek, events):
        week = ''
        for d, weekday in theweek:
            week += self.formatday(d, events)
        return f'<tr> {week} </tr>'

    # formats a month as a table
    # filter events by year and month
    def formatmonth(self, withyear=True):
        events = FreeDaysModel.objects.filter(principal=self.director).filter(start_time__year=self.year,
                                                                              start_time__month=self.month)

        cal = f'<table border="0" cellpadding="0" cellspacing="0" class="calendar">\n'
        cal += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
        cal += f'{self.formatweekheader()}\n'
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f'{self.formatweek(week, events)}\n'
        return cal


class CalendarKid(LoginRequiredMixin, View):
    def get(self, request, pk):
        permissions = request.user.get_user_permissions()
        month_number = int(timezone.now().month)
        year = int(timezone.now().year)
        kid = Kid.objects.get(id=int(pk))
        cal = Calendar(year=year, month=month_number, director=request.user.director, kid=kid).formatmonth(
            withyear=True)
        messages.info(request,f'{permissions}')
        return render(request, 'calendar.html', {'cal': mark_safe(cal)})

    def post(self, request, pk):
        presence = request.POST.get('presence')
        presence = presence.split(' ')
        presence_type = presence.pop(-1)
        month_name = presence[1]
        month_number = datetime.strptime(month_name, '%B').month
        presence[1] = f'{month_number}'
        presence.reverse()
        presence = '-'.join(presence)
        presence_type = presenceChoices[int(presence_type)][0]
        kid = Kid.objects.get(id=int(pk))
        test = PresenceModel.objects.filter(kid=kid).filter(day=presence).first()
        if test:
            test.presenceType = presence_type
            test.save()
        else:
            PresenceModel.objects.create(day=presence, kid=Kid.objects.get(id=int(pk)), presenceType=presence_type)
        messages.success(request, f"Zmieniono obecnosc")
        return redirect('calendar', pk=pk)


class Home(View):
    def get(self, request):
        # users = User.objects.get(email=f"{request.user.email}"
        return render(request, 'home.html')


class PostListView(ListView):
    model = Post
    template_name = 'post_list.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 5


class PostDetailView(DetailView):
    model = Post
    template_name = 'post_detail.html'
    context_object_name = 'post'


class PostCreateView(PermissionRequiredMixin, CreateView):
    permission_required = ("director.is_director", 'teacher.is_teacher')
    model = Post
    fields = ['title', 'content', 'image']
    template_name = 'post_form.html'

    def get_form(self, form_class=None):
        form = super(PostCreateView, self).get_form(form_class)
        form.fields['image'].required = False
        return form

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    permission_required = ("director.is_director", 'teacher.is_teacher')
    model = Post
    fields = ['title', 'content', 'image']
    template_name = 'post_form.html'

    def get_form(self, form_class=None):
        form = super(PostUpdateView, self).get_form(form_class)
        form.fields['image'].required = False
        return form

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


class PostDeleteView(PermissionRequiredMixin, UserPassesTestMixin, DeleteView):
    permission_required = "director.is_director"
    model = Post
    template_name = 'post_delete_confirm.html'
    context_object_name = 'post'
    success_url = '/wydarzenia/'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False
