from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from .forms import PaymentPlanForm
from .models import PaymentPlan
from django.core.exceptions import PermissionDenied
from director.models import Director
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import (
    CreateView,
)


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
from django.contrib.auth.mixins import PermissionRequiredMixin
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
