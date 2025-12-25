from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.utils import timezone
from .forms import PaymentPlanForm
from .models import PaymentPlan, SalaryPayment
from django.core.exceptions import PermissionDenied
from director.models import Director
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import (
    CreateView,
)
from django.db.models import Q, Sum
from datetime import date
from children.models import PresenceModel, Invoice, Kid
from parent.models import ParentA
from teacher.models import Employee

# Create your views here.
class AddPaymentsPlanView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    permission_required = "director.is_director"
    model = PaymentPlan
    template_name = 'payment-plan-add.html'
    form_class = PaymentPlanForm
    success_url = reverse_lazy('list_payments_plans')
    success_message = "Plan platnicz dodany porpawnie"

    def get_initial(self):
        initial = super(AddPaymentsPlanView, self).get_initial()
        initial = initial.copy()
        initial['principal'] = Director.objects.get(user=self.request.user.id)
        return initial

    def form_valid(self, form):
        form.instance.save()
        return super().form_valid(form)


# payments_plans/views.py
from django.db.models import Avg, Count

from django.db.models import Q, Avg, Count

class PaymentPlansListView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        director = request.user.director
        # Podstawowy QuerySet planów tego dyrektora
        payments_plans = PaymentPlan.objects.filter(principal=director).order_by('-id')

        # 1. Pobieranie parametrów z filtrów
        search_query = request.GET.get('search', '')
        frequency_filter = request.GET.get('frequency', '')
        status_filter = request.GET.get('status', '')

        # 2. Logika filtrowania tekstu (szukaj w nazwie)
        if search_query:
            payments_plans = payments_plans.filter(name__icontains=search_query)

        # 3. Logika filtrowania częstotliwości
        if frequency_filter:
            payments_plans = payments_plans.filter(frequency=frequency_filter)

        # 4. Logika filtrowania statusu
        if status_filter == 'active':
            payments_plans = payments_plans.filter(is_active=True, is_archived=False)
        elif status_filter == 'archived':
            payments_plans = payments_plans.filter(is_archived=True)
        elif status_filter == 'inactive':
            payments_plans = payments_plans.filter(is_active=False)

        # Statystyki (obliczane po filtracji lub na całości - zazwyczaj na całości placówki)
        stats_plans = PaymentPlan.objects.filter(principal=director, is_active=True)
        avg_price = stats_plans.aggregate(Avg('price'))['price__avg'] or 0
        most_popular = stats_plans.annotate(kids_num=Count('kid')).order_by('-kids_num').first()

        # Paginacja
        paginator = Paginator(payments_plans, 10)
        page_obj = paginator.get_page(request.GET.get('page'))

        context = {
            'page_obj': page_obj,
            'total_plans': stats_plans.count(),
            'avg_price': round(avg_price, 2),
            'most_popular': most_popular,
            # Przekazujemy wartości filtrów z powrotem do szablonu, by zachować stan pól
            'current_search': search_query,
            'current_frequency': frequency_filter,
            'current_status': status_filter,
        }
        return render(request, 'payments-plans-list.html', context)

class PaymentPlanUpdateView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request, pk):
        director = request.user.director
        plan = get_object_or_404(PaymentPlan, id=pk, principal=director)
        form = PaymentPlanForm(instance=plan)
        return render(request, 'payment-plan-update.html', {'form': form, 'plan': plan})

    def post(self, request, pk):
        director = request.user.director
        plan = get_object_or_404(PaymentPlan, id=pk, principal=director)
        form = PaymentPlanForm(request.POST, instance=plan)

        if form.is_valid():
            form.save()
            messages.success(request, 'Poprawnie zaktualizowano plan płatniczy.')
            return redirect('payment_plan_details', pk=plan.id)

        # Jeśli są błędy, renderujemy stronę ponownie (nie redirect!)
        return render(request, 'payment-plan-update.html', {'form': form, 'plan': plan})


class PaymentPlanDeleteView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request, pk):
        raise PermissionDenied

    def post(self, request, pk):
        payment = get_object_or_404(PaymentPlan, id=int(pk))
        director = Director.objects.get(user=request.user.id)
        if payment.principal == director:
            for kid in payment.kid_set.filter(is_active=True):
                kid.payment_plan = None
                kid.save()
            payment.delete()
            messages.success(request,
                             f'Popprawnie usunieto plan platniczy {payment}')
            return redirect('list_payments_plans')
        raise PermissionDenied


# payments_plans/views.py
from django.db.models import Sum, Count
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from .models import PaymentPlan

class PaymentPlanDetailsView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request, pk):
        director = request.user.director
        # Pobieranie planu przypisanego do dyrektora
        plan = get_object_or_404(PaymentPlan, id=pk, principal=director)

        # Pobieranie dzieci z podziałem na statusy
        all_enrolled = plan.kid_set.all().select_related('group')
        active_kids = all_enrolled.filter(is_active=True)
        past_kids = all_enrolled.filter(is_active=False)

        # Statystyki finansowe
        kids_count = active_kids.count()
        projected_revenue = kids_count * plan.price

        context = {
            'plan': plan,
            'active_kids': active_kids,
            'past_kids': past_kids,
            'kids_count': kids_count,
            'projected_revenue': projected_revenue,
            'capacity_percent': min(int((kids_count / 15) * 100), 100) if 15 > 0 else 0, # Przykładowy limit 15 miejsc
        }
        return render(request, 'payment-plan-details.html', context)



from django.core.paginator import Paginator

class ParentPaymentsView(LoginRequiredMixin, View):
    def get(self, request):
        parent = get_object_or_404(ParentA, user=request.user)

        # Pobieramy parametry z adresu URL
        kid_id = request.GET.get('kid_id')
        sort_order = request.GET.get('sort', 'desc') # Domyślnie najnowsze

        # Bazowy QuerySet
        invoices_qs = Invoice.objects.filter(kid__parenta=parent).select_related('kid', 'kid__kid_meals')

        # Filtrowanie po dziecku
        if kid_id and kid_id.isdigit():
            invoices_qs = invoices_qs.filter(kid_id=int(kid_id))

        # Sortowanie
        if sort_order == 'asc':
            invoices_qs = invoices_qs.order_by('year', 'month')
        else:
            invoices_qs = invoices_qs.order_by('-year', '-month')

        # Logika obliczania dni (zamiast filtra divide)
        for invoice in invoices_qs:
            if invoice.kid.kid_meals and invoice.kid.kid_meals.per_day > 0:
                invoice.calculated_days = int(invoice.meals_amount / invoice.kid.kid_meals.per_day)
            else:
                invoice.calculated_days = 0

        # Paginacja
        paginator = Paginator(invoices_qs, 4)
        page_obj = paginator.get_page(request.GET.get('page'))

        # Statystyki i lista dzieci do filtra
        my_kids = parent.kids.all()
        total_unpaid = invoices_qs.exclude(status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        return render(request, 'parent-payments.html', {
            'page_obj': page_obj,
            'my_kids': my_kids,
            'total_unpaid': total_unpaid,
            'selected_kid': int(kid_id) if kid_id and kid_id.isdigit() else None,
            'selected_sort': sort_order
        })

    def post(self, request):
        invoice_id = request.POST.get('invoice_id')
        invoice = get_object_or_404(Invoice, id=invoice_id)

        invoice.paid_amount = invoice.total_amount
        invoice.status = 'paid'
        invoice.save()

        messages.success(request, f"Płatność za miesiąc {invoice.month}/{invoice.year} została zaksięgowana.")
        return redirect('parent_payments')

from dateutil.relativedelta import relativedelta
class DirectorFinanceSummaryView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'director.is_director'

    def get(self, request):
        director = get_object_or_404(Director, user=request.user)
        today = date.today()

        # Pobieranie wybranego okresu z GET lub domyślnie poprzedni miesiąc
        selected_month = int(request.GET.get('month', (today - relativedelta(months=1)).month))
        selected_year = int(request.GET.get('year', (today - relativedelta(months=1)).year))

        # Filtrowanie danych
        invoices_qs = Invoice.objects.filter(principal=director, month=selected_month, year=selected_year)
        salaries_qs = SalaryPayment.objects.filter(principal=director, month=selected_month, year=selected_year)

        # Statystyki Przychody
        total_expected = invoices_qs.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        total_received = invoices_qs.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0

        # Statystyki Koszty - TUTAJ POPRAWKA
        total_salaries_to_pay = salaries_qs.aggregate(Sum('base_salary'))['base_salary__sum'] or 0
        # Sumujemy tylko te rekordy, gdzie is_paid == True
        total_salaries_paid = salaries_qs.filter(is_paid=True).aggregate(Sum('base_salary'))['base_salary__sum'] or 0

        # Paginacja (Dłużnicy i Pracownicy)
        debtors_paginator = Paginator(invoices_qs.exclude(status='paid').select_related('kid'), 5)
        salaries_paginator = Paginator(salaries_qs.select_related('employee'), 5)

        # Pełna lista miesięcy dla selecta
        months_list = [
            (1, 'Styczeń'), (2, 'Luty'), (3, 'Marzec'), (4, 'Kwiecień'),
            (5, 'Maj'), (6, 'Czerwiec'), (7, 'Lipiec'), (8, 'Sierpień'),
            (9, 'Wrzesień'), (10, 'Październik'), (11, 'Listopad'), (12, 'Grudzień')
        ]

        context = {
            'total_income': total_expected,
            'received_income': total_received,
            'total_salaries': total_salaries_to_pay,
            'salaries_paid': total_salaries_paid, # Przekazujemy poprawną wartość
            'balance': total_received - total_salaries_paid,
            'debtors': debtors_paginator.get_page(request.GET.get('d_page')),
            'salaries_list': salaries_paginator.get_page(request.GET.get('s_page')),
            'selected_month': selected_month,
            'selected_year': selected_year,
            'months_list': months_list, # Przekazujemy listę do pętli w HTML
        }
        return render(request, 'director-finance.html', context)
    def post(self, request):
        director = get_object_or_404(Director, user=request.user)
        action = request.POST.get('action')

        # Pobieramy datę za jaką mamy generować (z formularza ukryte pola)
        m_raw = request.POST.get('month') or request.GET.get('month')
        y_raw = request.POST.get('year') or request.GET.get('year')

        # Bezpieczna konwersja
        m = int(m_raw) if m_raw else timezone.now().month
        y = int(y_raw) if y_raw else timezone.now().year

        if action == 'generate_all':
            # 1. NAUCZYCIELE: Aktualizacja lub utworzenie
            teachers = Employee.objects.filter(principal=director, is_active=True)
            for t in teachers:
                SalaryPayment.objects.update_or_create(
                    principal=director, employee=t, month=m, year=y,
                    defaults={'base_salary': t.salary or 0}
                )

            # 2. DZIECI: Przeliczenie obecności i aktualizacja faktur
            first_day_of_month = date(y, m, 1)
            if m == 12:
                last_day_of_month = date(y, 12, 31)
            else:
                last_day_of_month = date(y, m + 1, 1) - relativedelta(days=1)
            kids = Kid.objects.filter(
                principal=director,
                is_active=True,
                start__lte=last_day_of_month
            ).filter(
                Q(end__isnull=True) | Q(end__gte=first_day_of_month)
            )
            for k in kids:
                billable_days = PresenceModel.objects.filter(
                    kid=k, day__month=m, day__year=y,
                    presenceType__in=[1, 2, 4]
                ).count()

                meals_total = billable_days * (k.kid_meals.per_day if k.kid_meals else 0)
                tuition = k.payment_plan.price if k.payment_plan else 0
                total = tuition + meals_total

                # Używamy update_or_create, aby zaktualizować kwoty jeśli faktura już była
                Invoice.objects.update_or_create(
                    kid=k, month=m, year=y, principal=director,
                    defaults={
                        'tuition_amount': tuition,
                        'meals_amount': meals_total,
                        'total_amount': total,
                        'due_date': date(y, m, 10) if m != 12 else date(y+1, 1, 10)
                    }
                )
            messages.success(request, f"Zaktualizowano rozliczenia za {m}/{y}")

        elif action == 'pay_salary':
                salary_id = request.POST.get('salary_id')
                salary = get_object_or_404(SalaryPayment, id=salary_id, principal=director)
                salary.is_paid = True
                salary.payment_date = date.today()
                salary.save()

        return redirect(f'/podsumowanie-finansowe/?month={m}&year={y}')
