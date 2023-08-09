from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from teacher.models import Employee
from .forms import KidAddForm, PaymentPlanForm, MealsForm, GroupsForm
from .models import Kid, Groups, PaymentPlan, Director, Meals
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin, LoginRequiredMixin
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
)


# Create your views here.
class AddPaymentsPlanView(PermissionRequiredMixin, CreateView):
    permission_required = "director.is_director"
    model = PaymentPlan
    template_name = 'payment-plan-add.html'
    form_class = PaymentPlanForm
    success_url = reverse_lazy('list_payments_plans')

    def get_initial(self):
        initial = super(AddPaymentsPlanView, self).get_initial()
        initial = initial.copy()
        initial['principal'] = Director.objects.get(user=self.request.user.id)
        return initial

    def form_valid(self, form):
        form.instance.save()
        return super().form_valid(form)


class PaymentPlansListView(PermissionRequiredMixin, ListView):
    permission_required = "director.is_director"
    model = PaymentPlan
    template_name = 'payments-plans-list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["plans"] = Director.objects.get(user=self.request.user.id).paymentplan_set.all()
        return context


class AddMealView(PermissionRequiredMixin, CreateView):
    permission_required = "director.is_director"
    model = Meals
    template_name = 'meal-add.html'
    form_class = MealsForm
    success_url = reverse_lazy('list_meals')

    def get_initial(self):
        initial = super(AddMealView, self).get_initial()
        initial = initial.copy()
        initial['principal'] = Director.objects.get(user=self.request.user.id)
        return initial

    def form_valid(self, form):
        form.instance.save()
        return super().form_valid(form)


class MealsListView(PermissionRequiredMixin, ListView):
    permission_required = "director.is_director"
    model = Meals
    template_name = 'meals-list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meals"] = Director.objects.get(user=self.request.user.id).meals_set.all()
        return context


class AddGroupView(PermissionRequiredMixin, CreateView):
    permission_required = "director.is_director"
    model = Groups
    template_name = 'group-add.html'
    form_class = GroupsForm
    success_url = reverse_lazy('list_groups')

    def get_initial(self):
        initial = super(AddGroupView, self).get_initial()
        initial = initial.copy()
        initial['principal'] = Director.objects.get(user=self.request.user.id)
        return initial

    def get_form(self, form_class=None):
        form = super(AddGroupView, self).get_form(form_class)
        return form

    def form_valid(self, form):
        form.instance.save()
        return super().form_valid(form)


class GroupsListView(PermissionRequiredMixin, ListView):
    permission_required = "director.is_director"
    model = Groups
    template_name = 'groups-list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["groups"] = Groups.objects.filter(principal=Director.objects.get(user=self.request.user.id)).all()
        return context


class AddKidView(PermissionRequiredMixin, UserPassesTestMixin, CreateView):
    permission_required = "director.is_director"
    model = Kid
    template_name = 'kid-add.html'
    form_class = KidAddForm
    success_url = reverse_lazy('list_kids')

    def get_initial(self):
        initial = super(AddKidView, self).get_initial()
        initial = initial.copy()
        initial['principal'] = Director.objects.get(user=self.request.user.id)
        return initial

    def get_form_kwargs(self, **kwargs):
        """ Passes the request object to the form class.
         This is necessary to only display members that belong to a given user"""

        kwargs = super(AddKidView, self).get_form_kwargs()
        kwargs.update({'current_user': self.request.user})
        return kwargs

    def get_form(self, form_class=None):
        form = super(AddKidView, self).get_form(form_class)
        form.fields['end'].required = False
        return form

    def form_valid(self, form):
        form.instance.save()
        return super().form_valid(form)

    def test_func(self):
        director = Director.objects.get(user=self.request.user.id)
        if director.groups_set.all():
            if director.meals_set.all():
                if director.paymentplan_set.all():
                    return True
        return False

    def handle_no_permission(self):
        director = Director.objects.get(user=self.request.user.id)
        if not director.groups_set.all():
            messages.error(self.request, 'Dodaj najpierw jakas grupe')
            return redirect('add_group')
        if not director.meals_set.all():
            messages.error(self.request, 'Dodaj najpierw jakis posilke')
            return redirect('add_meal')
        if not director.paymentplan_set.alL():
            messages.error(self.request, 'Dodaj najpierw jakis plan platniczy')
            return redirect('add_payment_plans')

        return redirect('add_meal')


class KidsListView(PermissionRequiredMixin, ListView):
    permission_required = "director.is_director"
    model = Kid
    template_name = 'kids-list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["kids"] = Director.objects.get(user=self.request.user.id).kid_set.all()
        return context


class DetailsKidView(PermissionRequiredMixin, UserPassesTestMixin, DetailView):
    permission_required = "director.is_director"
    model = Kid
    template_name = 'kid-details.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context["kid"] = get_object_or_404(Director, user=self.request.user.id).kid_set.get(id=context['kid'].id)
        except Exception:
            context["kid"] = None
        return context

    def test_func(self):
        kid = self.get_object()
        if self.request.user == kid.principal.user:
            return True
        return False


class ChangeKidInfoView(PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    permission_required = "director.is_director"
    model = Kid
    template_name = 'kid-update-info.html'
    form_class = KidAddForm
    success_url = reverse_lazy('list_kids')

    def get_form_kwargs(self, **kwargs):
        """ Passes the request object to the form class.
         This is necessary to only display members that belong to a given user"""

        kwargs = super(ChangeKidInfoView, self).get_form_kwargs()
        kwargs.update({'current_user': self.request.user})
        return kwargs

    def form_valid(self, form):
        form.instance.save()
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super(ChangeKidInfoView, self).get_form(form_class)
        form.fields['end'].required = False
        return form

    def test_func(self):
        kid = self.get_object()
        if self.request.user == kid.principal.user:
            return True
        return False


class KidSearchView(LoginRequiredMixin, View):
    def get(self, request):
        return redirect('list_kids')

    def post(self, request):
        search = request.POST.get('search')
        if search:
            kids = Kid.objects.filter(principal=Director.objects.get(user=request.user.id)).filter(
                first_name__icontains=search)
            return render(request, 'kids-list.html', {'kids': kids})
        return redirect('list_kids')


class GroupDetailsView(LoginRequiredMixin, View):
    def get(self, request, pk):
        group = Groups.objects.get(id=int(pk))
        teachers = list(group.employee_set.values_list("user__email", flat=True))
        kids = group.kid_set.all()

        if request.user.get_user_permissions() == {'teacher.is_teacher'}:
            teacher_email = Employee.objects.get(user=request.user.id).user.email
            if teacher_email in teachers:
                return render(request, 'group-details.html',
                              {'group': group, 'teachers': teachers, 'kids': kids})
        elif request.user.get_user_permissions() == {'director.is_director'}:
            director = Director.objects.get(user=request.user.id)
            if director == group.principal:
                return render(request, 'group-details.html',
                              {'group': group, 'teachers': teachers, 'kids': kids})

        messages.error(request, 'Nie masz pozwolenia')
        return redirect('home_page')


class GroupUpdateView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request, pk):
        group = Groups.objects.get(id=int(pk))
        director = Director.objects.get(user=request.user.id)
        if director == group.principal:
            form = GroupsForm(instance=group)
            return render(request, 'group-update.html', {'form': form})
        return redirect('list_groups')

    def post(self, request, pk):
        pass

