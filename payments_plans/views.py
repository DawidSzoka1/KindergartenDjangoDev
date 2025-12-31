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
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.views.generic import (
    CreateView,
)
from django.db.models import Q, Sum
from datetime import date
from children.models import PresenceModel, Invoice, Kid
from parent.models import ParentA
from teacher.models import Employee
from blog.views import get_active_context


# Create your views here.
class AddPaymentsPlanView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = PaymentPlan
    template_name = 'payment-plan-add.html'
    form_class = PaymentPlanForm
    success_url = reverse_lazy('list_payments_plans')
    success_message = "Plan płatniczy został dodany poprawnie."

    def get_form_kwargs(self):
        """Przekazujemy k_id do formularza (jeśli jest potrzebne do filtrowania)."""
        kwargs = super().get_form_kwargs()
        role, profile_id, k_id = get_active_context(self.request)
        kwargs['active_principal_id'] = k_id
        return kwargs

    def form_valid(self, form):
        # Pobieramy kontekst placówki
        role, profile_id, k_id = get_active_context(self.request)

        if role != 'director':
            raise PermissionDenied

        # Automatycznie przypisujemy plan do aktywnej placówki i profilu dyrektora
        form.instance.kindergarten_id = k_id
        form.instance.principal_id = profile_id  # Opcjonalnie, jeśli zostawiłeś to pole

        return super().form_valid(form)


# payments_plans/views.py
from django.db.models import Avg, Count

from django.db.models import Q, Avg, Count

class PaymentPlansListView(LoginRequiredMixin, View):
    def get(self, request):
        # Pobieramy aktywny kontekst sesji
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied

        # 1. Podstawowy QuerySet planów dla aktywnej placówki
        # Używamy managera .for_kindergarten(k_id) lub filtra po kindergarten_id
        payments_plans = PaymentPlan.objects.filter(kindergarten_id=k_id).order_by('-id')

        # 2. Pobieranie parametrów z filtrów
        search_query = request.GET.get('search', '')
        frequency_filter = request.GET.get('frequency', '')
        status_filter = request.GET.get('status', '')

        # 3. Logika filtrowania
        if search_query:
            payments_plans = payments_plans.filter(name__icontains=search_query)

        if frequency_filter:
            payments_plans = payments_plans.filter(frequency=frequency_filter)

        if status_filter == 'active':
            payments_plans = payments_plans.filter(is_active=True, is_archived=False)
        elif status_filter == 'archived':
            payments_plans = payments_plans.filter(is_archived=True)
        elif status_filter == 'inactive':
            payments_plans = payments_plans.filter(is_active=False)

        # 4. Statystyki obliczane dla CAŁEJ placówki (k_id)
        # Dzięki temu każdy dyrektor widzi te same globalne dane finansowe przedszkola
        stats_plans = PaymentPlan.objects.filter(kindergarten_id=k_id, is_active=True)

        avg_price = stats_plans.aggregate(Avg('price'))['price__avg'] or 0

        # Obliczamy popularność na podstawie dzieci przypisanych do planów w tej placówce
        most_popular = stats_plans.annotate(
            kids_num=Count('kid', filter=Q(kid__is_active=True))
        ).order_by('-kids_num').first()

        # Paginacja
        paginator = Paginator(payments_plans, 10)
        page_obj = paginator.get_page(request.GET.get('page'))

        context = {
            'page_obj': page_obj,
            'total_plans': stats_plans.count(),
            'avg_price': round(avg_price, 2),
            'most_popular': most_popular,
            'current_search': search_query,
            'current_frequency': frequency_filter,
            'current_status': status_filter,
        }
        return render(request, 'payments-plans-list.html', context)

class PaymentPlanUpdateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        # Pobieramy k_id z sesji użytkownika
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied

        # Szukamy planu w ramach aktywnej placówki
        plan = get_object_or_404(PaymentPlan, id=pk, kindergarten_id=k_id)

        # Przekazujemy k_id do formularza przez kwargs
        form = PaymentPlanForm(instance=plan, active_principal_id=k_id)

        return render(request, 'payment-plan-update.html', {'form': form, 'plan': plan})

    def post(self, request, pk):
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied

        plan = get_object_or_404(PaymentPlan, id=pk, kindergarten_id=k_id)

        # Przekazujemy dane POST oraz k_id do formularza
        form = PaymentPlanForm(request.POST, instance=plan, active_principal_id=k_id)

        if form.is_valid():
            form.save()
            messages.success(request, 'Poprawnie zaktualizowano plan płatniczy.')
            # Upewnij się, że nazwa widoku 'payment_plan_details' jest poprawna w urls.py
            return redirect('list_payments_plans')

        messages.error(request, "Popraw błędy w formularzu.")
        return render(request, 'payment-plan-update.html', {'form': form, 'plan': plan})


class PaymentPlanDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        raise PermissionDenied

    def post(self, request, pk):
        # Pobieramy kontekst placówki z sesji
        role, profile_id, k_id = get_active_context(request)

        # Weryfikacja roli dyrektora dla aktywnej placówki
        if role != 'director':
            raise PermissionDenied

        # Pobieramy plan, upewniając się, że należy do tej placówki
        payment = get_object_or_404(PaymentPlan, id=pk, kindergarten_id=k_id, is_active=True)

        # 1. Odłączamy plan od aktywnych dzieci w ramach tej placówki
        # Robimy to tylko dla dzieci przypisanych do tego przedszkola
        kids_with_plan = payment.kid_set.filter(is_active=True, kindergarten_id=k_id)

        # Masowa aktualizacja dla wydajności (bezpieczniejsza niż pętla for)
        kids_with_plan.update(payment_plan=None)

        # 2. Usuwanie logiczne (Soft Delete)
        # Zamiast usuwać rekord, oznaczamy go jako archiwalny/nieaktywny
        payment.is_active = False
        payment.is_archived = True
        payment.save()

        messages.success(request, f'Pomyślnie wycofano plan płatniczy: {payment.name}')
        return redirect('list_payments_plans')


# payments_plans/views.py
from django.db.models import Sum, Count
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from .models import PaymentPlan

class PaymentPlanDetailsView(LoginRequiredMixin, View):
    def get(self, request, pk):
        # Pobieramy kontekst placówki z sesji
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied

        # 1. Pobieranie planu przypisanego do placówki
        #
        plan = get_object_or_404(PaymentPlan, id=pk, kindergarten_id=k_id)

        # 2. Pobieranie dzieci - filtrujemy dodatkowo po kindergarten_id dla pewności
        all_enrolled = plan.kid_set.filter(kindergarten_id=k_id).select_related('group')

        active_kids = all_enrolled.filter(is_active=True).order_by('last_name')
        past_kids = all_enrolled.filter(is_active=False).order_by('-id')

        # 3. Statystyki finansowe
        kids_count = active_kids.count()
        projected_revenue = kids_count * plan.price

        context = {
            'plan': plan,
            'active_kids': active_kids,
            'past_kids': past_kids,
            'kids_count': kids_count,
            'projected_revenue': projected_revenue,
            # Przykładowy limit miejsc można pobrać z ustawień placówki lub zostawić jako stałą
            'capacity_percent': min(int((kids_count / 20) * 100), 100) if 20 > 0 else 0,
        }

        return render(request, 'payment-plan-details.html', context)



from django.core.paginator import Paginator
from django.db.models import Sum

class ParentPaymentsView(LoginRequiredMixin, View):
    def get(self, request):
        # Pobieramy aktywny kontekst sesji (rolę, ID profilu rodzica i ID placówki)
        role, profile_id, k_id = get_active_context(request)

        if role != 'parent':
            raise PermissionDenied

        # Pobieramy konkretny profil rodzica dla TEJ placówki
        parent = get_object_or_404(ParentA, id=profile_id, kindergarten_id=k_id)

        # Pobieramy parametry z adresu URL
        kid_id = request.GET.get('kid_id')
        sort_order = request.GET.get('sort', 'desc')

        # Bazowy QuerySet faktur ograniczony do dzieci rodzica W TEJ placówce
        #
        invoices_qs = Invoice.objects.filter(
            kid__parenta=parent,
            kid__kindergarten_id=k_id
        ).select_related('kid', 'kid__kid_meals')

        # Filtrowanie po dziecku (dodatkowa weryfikacja czy dziecko należy do k_id)
        if kid_id and kid_id.isdigit():
            invoices_qs = invoices_qs.filter(kid_id=int(kid_id), kid__kindergarten_id=k_id)

        # Sortowanie
        if sort_order == 'asc':
            invoices_qs = invoices_qs.order_by('year', 'month')
        else:
            invoices_qs = invoices_qs.order_by('-year', '-month')

        # Logika obliczania dni (bez zmian, ale bezpieczna dzięki select_related)
        for invoice in invoices_qs:
            if invoice.kid.kid_meals and invoice.kid.kid_meals.per_day > 0:
                invoice.calculated_days = int(invoice.meals_amount / invoice.kid.kid_meals.per_day)
            else:
                invoice.calculated_days = 0

        # Paginacja
        paginator = Paginator(invoices_qs, 4)
        page_obj = paginator.get_page(request.GET.get('page'))

        # Statystyki i lista dzieci (tylko z tej placówki)
        my_kids = parent.kids.filter(kindergarten_id=k_id, is_active=True)
        total_unpaid = invoices_qs.exclude(status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        return render(request, 'parent-payments.html', {
            'page_obj': page_obj,
            'my_kids': my_kids,
            'total_unpaid': total_unpaid,
            'selected_kid': int(kid_id) if kid_id and kid_id.isdigit() else None,
            'selected_sort': sort_order
        })

    def post(self, request):
        role, profile_id, k_id = get_active_context(request)

        if role != 'parent':
            raise PermissionDenied

        invoice_id = request.POST.get('invoice_id')
        # Krytyczne: sprawdzamy czy faktura należy do dziecka w aktywnej placówce
        invoice = get_object_or_404(Invoice, id=invoice_id, kid__kindergarten_id=k_id)

        # Logika opłacania
        invoice.paid_amount = invoice.total_amount
        invoice.status = 'paid'
        invoice.save()

        messages.success(request, f"Płatność za miesiąc {invoice.month}/{invoice.year} została zaksięgowana.")
        return redirect('parent_payments')

from dateutil.relativedelta import relativedelta

from django.db.models import Sum, Q
from django.utils import timezone
from datetime import date
from dateutil.relativedelta import relativedelta

class DirectorFinanceSummaryView(LoginRequiredMixin, View):
    def get(self, request):
        # Pobieramy aktywny kontekst placówki
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied

        today = date.today()
        # Pobieranie wybranego okresu
        selected_month = int(request.GET.get('month', (today - relativedelta(months=1)).month))
        selected_year = int(request.GET.get('year', (today - relativedelta(months=1)).year))

        # Filtrowanie danych wyłącznie po k_id (placówce)
        invoices_qs = Invoice.objects.filter(kindergarten_id=k_id, month=selected_month, year=selected_year)
        salaries_qs = SalaryPayment.objects.filter(kindergarten_id=k_id, month=selected_month, year=selected_year)

        # Statystyki Przychody
        total_expected = invoices_qs.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        total_received = invoices_qs.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0

        # Statystyki Koszty
        total_salaries_to_pay = salaries_qs.aggregate(Sum('base_salary'))['base_salary__sum'] or 0
        total_salaries_paid = salaries_qs.filter(is_paid=True).aggregate(Sum('base_salary'))['base_salary__sum'] or 0

        # Paginacja
        debtors_paginator = Paginator(invoices_qs.exclude(status='paid').select_related('kid'), 5)
        salaries_paginator = Paginator(salaries_qs.select_related('employee', 'employee__user'), 5)

        months_list = [
            (1, 'Styczeń'), (2, 'Luty'), (3, 'Marzec'), (4, 'Kwiecień'),
            (5, 'Maj'), (6, 'Czerwiec'), (7, 'Lipiec'), (8, 'Sierpień'),
            (9, 'Wrzesień'), (10, 'Październik'), (11, 'Listopad'), (12, 'Grudzień')
        ]

        context = {
            'total_income': total_expected,
            'received_income': total_received,
            'total_salaries': total_salaries_to_pay,
            'salaries_paid': total_salaries_paid,
            'balance': total_received - total_salaries_paid,
            'debtors': debtors_paginator.get_page(request.GET.get('d_page')),
            'salaries_list': salaries_paginator.get_page(request.GET.get('s_page')),
            'selected_month': selected_month,
            'selected_year': selected_year,
            'months_list': months_list,
        }
        return render(request, 'director-finance.html', context)

    def post(self, request):
        role, profile_id, k_id = get_active_context(request)
        if role != 'director':
            raise PermissionDenied

        action = request.POST.get('action')
        m = int(request.POST.get('month', timezone.now().month))
        y = int(request.POST.get('year', timezone.now().year))

        if action == 'generate_all':
            # 1. NAUCZYCIELE: Filtrujemy po placówce
            teachers = Employee.objects.filter(kindergarten_id=k_id, is_active=True)
            for t in teachers:
                SalaryPayment.objects.update_or_create(
                    kindergarten_id=k_id, employee=t, month=m, year=y,
                    defaults={'base_salary': t.salary or 0}
                )

            # 2. DZIECI: Rozliczenie obecności w ramach placówki
            first_day = date(y, m, 1)
            last_day = first_day + relativedelta(day=31)

            kids = Kid.objects.filter(
                kindergarten_id=k_id,
                is_active=True,
                start__lte=last_day
            ).filter(
                Q(end__isnull=True) | Q(end__gte=first_day)
            )

            for k in kids:
                billable_days = PresenceModel.objects.filter(
                    kid=k, day__month=m, day__year=y,
                    presenceType__in=[1, 2, 4]
                ).count()

                meals_total = billable_days * (k.kid_meals.per_day if k.kid_meals else 0)
                tuition = k.payment_plan.price if k.payment_plan else 0
                total = tuition + meals_total

                Invoice.objects.update_or_create(
                    kid=k, month=m, year=y, kindergarten_id=k_id,
                    defaults={
                        'tuition_amount': tuition,
                        'meals_amount': meals_total,
                        'total_amount': total,
                        'due_date': (first_day + relativedelta(months=1, day=10))
                    }
                )
            messages.success(request, f"Zaktualizowano rozliczenia placówki za {m}/{y}")

        elif action == 'pay_salary':
            salary_id = request.POST.get('salary_id')
            # Weryfikujemy czy wypłata należy do tej placówki
            salary = get_object_or_404(SalaryPayment, id=salary_id, kindergarten_id=k_id)
            salary.is_paid = True
            salary.payment_date = date.today()
            salary.save()

        return redirect(f'/podsumowanie-finansowe/?month={m}&year={y}')
