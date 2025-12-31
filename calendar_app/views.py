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
from blog.views import get_active_context
import calendar as py_calendar


class Calendar(py_calendar.HTMLCalendar):
    def __init__(self, year=None, month=None, kid=None, kindergarten_id=None):
        self.year = int(year)
        self.month = int(month)
        self.kid = kid
        self.kindergarten_id = kindergarten_id
        super(Calendar, self).__init__()

        # Optymalizacja: Pobieramy wszystkie obecności i dni wolne raz dla całego miesiąca
        self.presences = self._get_monthly_presences()
        self.free_days = self._get_monthly_free_days()

    def _get_monthly_presences(self):
        """Pobiera obecności dziecka w danym miesiącu i zapisuje w słowniku {dzień: obiekt}."""
        presences = PresenceModel.objects.filter(
            kid=self.kid,
            day__year=self.year,
            day__month=self.month
        )
        return {p.day.day: p for p in presences}

    def _get_monthly_free_days(self):
        """Pobiera dni wolne placówki w danym miesiącu."""
        # Filtrujemy po placówce (kindergarten_id), a nie po dyrektorze
        return FreeDaysModel.objects.filter(
            kindergarten_id=self.kindergarten_id,
            start_time__year=self.year,
            start_time__month=self.month
        ).values_list('start_time__day', flat=True)

    def formatday(self, day, weekday):
        if day == 0:
            return '<div class="h-12 w-full"></div>'

        # Logika sprawdzania czy to weekend (sobota=5, niedziela=6)
        is_weekend = weekday in [5, 6]

        # Sprawdzanie czy to dzień wolny ustawiony przez placówkę
        is_free_day = day in self.free_days

        # Pobieranie obecności ze słownika (brak zapytań SQL w pętli)
        presence = self.presences.get(day)

        # Sprawdzanie czy to dzisiaj
        today = timezone.now().date()
        is_today = (today.year == self.year and today.month == self.month and today.day == day)

        # Klasy bazowe Tailwind
        css_classes = "h-12 w-full text-sm font-semibold rounded-xl transition-all flex items-center justify-center relative "

        if is_today:
            css_classes += "ring-2 ring-primary ring-offset-2 "

        if is_weekend or is_free_day:
            css_classes += "bg-gray-100 text-gray-400 dark:bg-gray-800 dark:text-gray-600 cursor-not-allowed "
        else:
            css_classes += "text-gray-700 dark:text-gray-300 hover:bg-primary/10 "

        # Nakładanie statusów kolorystycznych na podstawie typu obecności
        status_dot = ""
        if presence:
            if presence.presenceType == 1: # Nieobecność
                css_classes += "bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 "
                status_dot = '<span class="absolute bottom-1.5 size-1.5 bg-red-500 rounded-full"></span>'
            elif presence.presenceType == 2: # Obecność
                css_classes += "bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-400 "
                status_dot = '<span class="absolute bottom-1.5 size-1.5 bg-green-500 rounded-full"></span>'
            elif presence.presenceType == 3: # Planowana nieobecność
                css_classes += "bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 "
                status_dot = '<span class="absolute bottom-1.5 size-1.5 bg-blue-500 rounded-full"></span>'

        # Atrybut onclick lub data-day dla JavaScriptu do obsługi modala
        action_attr = f'onclick="openPresenceModal({day})"' if not (is_weekend or is_free_day) else ""

        return f'''
            <button type="button" {action_attr} class="{css_classes}">
                <span class="z-20">{day}</span>
                {status_dot}
            </button>
        '''

    def formatweek(self, theweek):
        week = ''
        for d, weekday in theweek:
            week += self.formatday(d, weekday)
        return f'<div class="grid grid-cols-7 gap-2">{week}</div>'

    def formatmonth(self, withyear=True):
        body = ""
        # monthdays2calendar zwraca listę tygodni, gdzie każdy tydzień to lista krotek (dzień, numer_dnia_tygodnia)
        for week in self.monthdays2calendar(self.year, self.month):
            body += self.formatweek(week)

        return body




from django.utils.safestring import mark_safe
from datetime import datetime

class CalendarKid(LoginRequiredMixin, View):
    def get(self, request, pk, month, year):
        # Pobieramy k_id (placówkę) z sesji
        role, profile_id, k_id = get_active_context(request)

        # 1. Pobieramy dziecko i sprawdzamy czy należy do AKTYWNEJ placówki
        kid = get_object_or_404(Kid, id=pk, kindergarten_id=k_id)

        if not kid.is_active:
            raise PermissionDenied("Profil dziecka jest nieaktywny.")

        # 2. Logika uprawnień (kto może widzieć kalendarz dziecka)
        has_access = False
        if role == 'director':
            has_access = True # get_object_or_404 powyżej już sprawdził k_id
        elif role == 'teacher':
            teacher = get_object_or_404(Employee, id=profile_id, kindergarten_id=k_id)
            if kid.group == teacher.group:
                has_access = True
        elif role == 'parent':
            parent = get_object_or_404(ParentA, id=profile_id, kindergarten_id=k_id)
            # Sprawdzamy czy to dziecko jest przypisane do tego profilu rodzica
            if kid in parent.kids.all():
                has_access = True

        if not has_access:
            raise PermissionDenied("Nie masz uprawnień do widoku kalendarza tego dziecka.")

        # 3. Logika kalendarza (obliczenia dat)
        month_number = int(month)
        year_number = int(year)
        month_name = py_calendar.month_name[month_number]
        day_current = timezone.now().day if timezone.now().month == month_number else None

        # Nawigacja miesiąca
        if month_number == 12:
            month_next, year_next = 1, year_number + 1
        else:
            month_next, year_next = month_number + 1, year_number

        if month_number == 1:
            month_previous, year_previous = 12, year_number - 1
        else:
            month_previous, year_previous = month_number - 1, year_number

        # Generowanie HTML kalendarza (zakładając Twoją klasę Calendar)
        cal = Calendar(year=year_number, month=month_number, kid=kid, kindergarten_id=k_id).formatmonth(withyear=True)

        context = {
            'cal': mark_safe(cal),
            'day_current': day_current,
            'kid': kid,
            'month': month_number,
            'year': year_number,
            'month_next': month_next,
            'year_next': year_next,
            'month_previous': month_previous,
            'year_previous': year_previous,
            'month_name': month_name,
            'active_role': role,
        }
        return render(request, 'calendar.html', context)

    def post(self, request, pk, month, year):
        role, profile_id, k_id = get_active_context(request)

        # Walidacja dziecka i placówki
        kid = get_object_or_404(Kid, id=pk, kindergarten_id=k_id)

        presence_type_id = request.POST.get('presence')
        day = request.POST.get('selected_day')

        try:
            selected_date = datetime.strptime(f"{year}-{month}-{day}", '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Nieprawidłowa data.")
            return redirect('calendar', pk=pk, month=month, year=year)

        today = timezone.now().date()

        # 1. BLOKADA: Rodzic może zmieniać tylko przyszłość/dzisiaj (zgłaszanie nieobecności)
        if role == 'parent':
            if selected_date < today:
                messages.error(request, "Rodzic nie może zmieniać statusów wstecz.")
                return redirect('calendar', pk=pk, month=month, year=year)

            # Walidacja typu obecności dla rodzica (np. tylko 3 - 'Zgłoszona nieobecność')
            if int(presence_type_id) not in [2, 3]: # Dostosuj do swojego modelu (np. obecny lub zgł. nieobecny)
                messages.error(request, "Nieprawidłowy typ zgłoszenia.")
                return redirect('calendar', pk=pk, month=month, year=year)

        # 2. Zapis statusu
        PresenceModel.objects.update_or_create(
            day=selected_date,
            kid=kid,
            defaults={'presenceType': int(presence_type_id)}
        )

        messages.success(request, f"Zaktualizowano status dla dnia {day}.{month}.{year}")
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
        # 1. Pobieramy kontekst placówki (k_id to Twój principal_id w sesji)
        role, profile_id, k_id = get_active_context(request)
        now = timezone.now()
        year, month = now.year, now.month

        # Obsługa weekendów
        if now.weekday() >= 5:
            return render(request, 'presence-calendar.html', {'weekend': True})

        # 2. Pobieranie QuerySetu dzieci w zależności od roli i AKTYWNEJ placówki
        if role == 'director':
            # Dyrektor widzi wszystkie dzieci w tej placówce
            kids_qs = Kid.objects.filter(kindergarten_id=k_id, is_active=True)
        elif role == 'teacher':
            # Nauczyciel widzi dzieci ze swojej grupy w tej placówce
            teacher = get_object_or_404(Employee, id=profile_id, kindergarten_id=k_id)
            if teacher.group:
                kids_qs = Kid.objects.filter(group=teacher.group, kindergarten_id=k_id, is_active=True)
            else:
                kids_qs = Kid.objects.none()
        elif role == 'parent':
            # Rodzic widzi swoje dzieci przypisane do tej placówki
            parent = get_object_or_404(ParentA, id=profile_id, kindergarten_id=k_id)
            kids_qs = parent.kids.filter(kindergarten_id=k_id, is_active=True)
        else:
            raise PermissionDenied

        # 3. Wyszukiwanie (przeniesione do GET dla poprawnej paginacji)
        search_query = request.GET.get('search', '').strip()
        if search_query:
            kids_qs = kids_qs.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )

        kids_qs = kids_qs.order_by('last_name', 'first_name')

        # 4. Paginacja
        paginator = Paginator(kids_qs, 10)
        page_obj = paginator.get_page(request.GET.get('page'))

        # 5. Budowanie mapy obecności (optymalizacja N+1)
        today_date = now.date()
        # Pobieramy obecności tylko dla dzieci widocznych na danej stronie paginacji
        presences = PresenceModel.objects.filter(day=today_date, kid__in=page_obj)
        presence_map = {p.kid_id: p for p in presences}

        kids_presence_dict = {kid: presence_map.get(kid.id) for kid in page_obj}

        tomorrow_date = today_date + timedelta(days=1)

        context = {
            'page_obj': page_obj,
            'dict': kids_presence_dict,
            'today': today_date,
            'year': year,
            'month': month,
            'tomorrow': tomorrow_date.weekday(),
            'search_query': search_query,
            'weekend': False,
            'active_role': role,
        }
        return render(request, 'presence-calendar.html', context)

    def post(self, request):
        role, profile_id, k_id = get_active_context(request)

        # Szybkie wyszukiwanie z POST przekierowujemy na GET
        if 'search_button' in request.POST:
            search = request.POST.get('search', '').strip()
            return redirect(f"{request.path}?search={search}")

        data_raw = request.POST.get('data')
        if not data_raw:
            return redirect('presence_calendar')

        try:
            data = data_raw.split()
            kid_id = int(data[0])
            p_type = int(data[1])
        except (IndexError, ValueError):
            return redirect('presence_calendar')

        # Pobieramy dziecko upewniając się, że należy do placówki w sesji
        kid = get_object_or_404(Kid, id=kid_id, kindergarten_id=k_id, is_active=True)

        # Logika daty i uprawnień
        if role == 'parent':
            # Rodzic może zgłosić obecność/nieobecność tylko na JUTRO
            parent = get_object_or_404(ParentA, id=profile_id, kindergarten_id=k_id)
            if kid not in parent.kids.all():
                raise PermissionDenied
            target_date = timezone.now().date() + timedelta(days=1)
        else:
            # Personel operuje na DZIŚ
            target_date = timezone.now().date()
            if role == 'teacher':
                teacher = get_object_or_404(Employee, id=profile_id, kindergarten_id=k_id)
                if kid.group != teacher.group:
                    raise PermissionDenied

        # Zapis/Aktualizacja
        PresenceModel.objects.update_or_create(
            day=target_date,
            kid=kid,
            defaults={'presenceType': p_type}
        )

        return redirect('presence_calendar')
