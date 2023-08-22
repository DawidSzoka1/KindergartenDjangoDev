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
    ListView,
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


class PaymentPlansListView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        payments_plans = PaymentPlan.objects.filter(principal__user=request.user).filter(is_active=True).order_by('-id')
        paginator = Paginator(payments_plans, 10)
        page = request.GET.get('page')
        page_obj = paginator.get_page(page)
        return render(request, 'payments-plans-list.html', {'page_obj': page_obj})


class PaymentPlanUpdateView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request, pk):
        payment = get_object_or_404(PaymentPlan, id=int(pk))
        director = Director.objects.get(user=request.user.id)
        if payment:
            if payment.principal == director:
                form = PaymentPlanForm(instance=payment)
                return render(request, 'payment-plan-update.html', {'form': form})
        raise PermissionDenied

    def post(self, request, pk):
        payment = get_object_or_404(PaymentPlan, id=int(pk))
        form = PaymentPlanForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Poprawnie zmieniono informacje')
            return redirect('list_payments_plans')
        messages.error(request, f"{form.errors}")
        return redirect('payment_plan_update', pk=pk)


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
