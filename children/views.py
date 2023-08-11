from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from teacher.models import Employee
from django.contrib.messages.views import SuccessMessageMixin
from .forms import KidAddForm, PaymentPlanForm, GroupsForm
from .models import Kid, Groups, PaymentPlan, Meals
from django.core.exceptions import PermissionDenied
from director.models import Director, MealPhotos, GroupPhotos
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin, LoginRequiredMixin
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
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


class PaymentPlansListView(PermissionRequiredMixin, ListView):
    permission_required = "director.is_director"
    model = PaymentPlan
    template_name = 'payments-plans-list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["plans"] = Director.objects.get(user=self.request.user.id).paymentplan_set.filter(is_active=True)
        return context


class PaymentPlanUpdateView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request, pk):
        return render(request, 'payment-plan-update.html')

    def post(self, request, pk):
        pass


class MealAddView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        director = Director.objects.get(user=request.user.id)
        photos = director.mealphotos_set.filter(is_active=True)
        if photos:
            return render(request, 'meal-add.html', {'photos': photos})
        messages.info(request, 'Najpierwsz musisz dodac jakas iconke')
        return redirect('photo_add')

    def post(self, request):
        director = request.user.director
        photo_id = request.POST.get('photo')
        per_day = request.POST.get('per_day')
        name = request.POST.get('name')
        description = request.POST.get('description')
        image = MealPhotos.objects.get(id=int(photo_id))
        if image and name and description and per_day:
            new_meal = Meals.objects.create(name=name, description=description, principal=director,
                                            per_day=float(per_day))
            new_meal.photo.add(image)
        elif image and name and per_day:
            new_meal = Meals.objects.create(name=name, principal=director, per_day=float(per_day))
            new_meal.photo.add(image)

        else:
            messages.error(request, 'Wszystkie pola musza byc wypelnione')
            return redirect('add_meal')

        messages.success(request, f'poprawnie dodano posilek o nazwie {new_meal.name}')
        return redirect('list_meals')


class MealsListView(PermissionRequiredMixin, ListView):
    permission_required = "director.is_director"
    model = Meals
    template_name = 'meals-list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meals"] = Director.objects.get(user=self.request.user.id).meals_set.filter(is_active=True)
        return context


class MealsUpdateView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request, pk):
        director = Director.objects.get(user=request.user.id)
        meal = Meals.objects.filter(is_active=True).filter(id=int(pk)).filter(principal=director).first()
        if meal:
            current_photo = meal.photo.first()
            photos = director.mealphotos_set.filter(is_active=True)
            return render(request, 'meal-update.html',
                          {
                              'meal': meal,
                              'current_photo': current_photo,
                              'photos': photos
                          })
        raise PermissionDenied

    def post(self, request, pk):
        name = request.POST.get("name")
        description = request.POST.get("description")
        per_day = request.POST.get("per_day")
        photo = request.POST.get("photo")
        meal = Meals.objects.filter(is_active=True).filter(id=int(pk)).first()
        if meal:
            if name and description and per_day and photo:
                meal.name = name
                meal.description = description
                meal.per_day = per_day
                meal.photo.clear()
                meal.photo.add(photo)
                meal.save()
                return redirect('list_meals')
            messages.error(request, "Wypelnij wszystkie pola")
            return redirect('meals_update', pk=pk)
        raise PermissionDenied


class GroupAddView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        director = Director.objects.get(user=request.user.id)
        photos = director.groupphotos_set.filter(is_active=True)
        if photos:
            return render(request, 'group-add.html', {'photos': photos})
        return redirect('photo_add')

    def post(self, request):
        director = Director.objects.get(user=request.user.id)
        photo_id = request.POST.get('photo')
        name = request.POST.get('name')
        capacity = request.POST.get('capacity')
        if photo_id and name and capacity:
            if '-' in capacity:
                messages.error(request, 'pojemnosc nie moze byc ujemna')
                return redirect('add_group')
            else:
                image = GroupPhotos.objects.get(id=int(photo_id))
                new_group = Groups.objects.create(name=name, capacity=int(capacity), principal=director)
                new_group.photo.add(image)
                messages.success(request, f'poprawnie dodano grupe o nazwie {new_group.name}')
                return redirect('list_groups')
        messages.error(request, 'Wszystkie pola musza byc wypelnione')
        return redirect('add_group')


class GroupsListView(PermissionRequiredMixin, ListView):
    permission_required = "director.is_director"
    model = Groups
    template_name = 'groups-list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["groups"] = Groups.objects.filter(principal=Director.objects.get(user=self.request.user.id)).filter(
            is_active=True)
        return context


class GroupDetailsView(LoginRequiredMixin, View):
    def get(self, request, pk):
        group = Groups.objects.get(id=int(pk))
        teachers = list(group.employee_set.filter(is_active=True).values_list("user__email", flat=True))
        kids = group.kid_set.filter(is_active=True)

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

        raise PermissionDenied


class GroupUpdateView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request, pk):
        group = Groups.objects.get(id=int(pk))
        director = Director.objects.get(user=request.user.id)
        group.photo.filter(is_active=True).first()
        if director == group.principal:
            form = GroupsForm(instance=group)
            photos = director.groupphotos_set.filter(is_active=True)
            return render(request, 'group-update.html',
                          {'form': form, 'photos': photos, 'group_photo': group.photo.first()})
        raise PermissionDenied

    def post(self, request, pk):
        group = Groups.objects.get(id=int(pk))
        director = Director.objects.get(user=request.user.id)
        if director == group.principal:
            form = GroupsForm(request.POST, instance=group)
            if form.is_valid():
                form.save()
                return redirect('group_details', pk=group.id)

            messages.error(request, f'{form.errors}')
            return redirect('group_update', pk=pk)

        raise PermissionDenied


class AddKidView(PermissionRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, CreateView):
    permission_required = "director.is_director"
    model = Kid
    template_name = 'kid-add.html'
    form_class = KidAddForm
    success_url = reverse_lazy('list_kids')
    success_message = "Dodano poprawni dziecko"

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
        if director.groups_set.filter(is_active=True):
            if director.meals_set.filter(is_active=True):
                if director.paymentplan_set.filter(is_active=True):
                    return True
        return False

    def handle_no_permission(self):
        director = Director.objects.get(user=self.request.user.id)
        if not director.groups_set.filter(is_active=True):
            messages.error(self.request, 'Dodaj najpierw jakas grupe')
            return redirect('add_group')
        if not director.meals_set.filter(is_active=True):
            messages.error(self.request, 'Dodaj najpierw jakis posilke')
            return redirect('add_meal')
        if not director.paymentplan_set.filter(is_active=True):
            messages.error(self.request, 'Dodaj najpierw jakis plan platniczy')
            return redirect('add_payment_plans')

        return redirect('add_meal')


class KidsListView(PermissionRequiredMixin, ListView):
    permission_required = "director.is_director"
    model = Kid
    template_name = 'kids-list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["kids"] = Director.objects.get(user=self.request.user.id).kid_set.filter(is_active=True)
        return context


class DetailsKidView(PermissionRequiredMixin, UserPassesTestMixin, DetailView):
    permission_required = "director.is_director"
    model = Kid
    template_name = 'kid-details.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context["kid"] = get_object_or_404(Director, user=self.request.user.id).kid_set.filter(
                is_active=True).filter(id=context['kid'].id).first()
            context["meals"] = context['kid'].kid_meals.filter(is_active=True)
            context["parents"] = context['kid'].parenta_set.filter(is_active=True)
        except Exception:
            raise PermissionDenied
        return context

    def test_func(self):
        kid = self.get_object()
        if self.request.user == kid.principal.user:
            return True
        return False


class ChangeKidInfoView(PermissionRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    permission_required = "director.is_director"
    model = Kid
    template_name = 'kid-update-info.html'
    form_class = KidAddForm
    success_url = reverse_lazy('list_kids')
    success_message = "poprawni zmieniono informacje"

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
                is_active=True).filter(
                first_name__icontains=search)
            return render(request, 'kids-list.html', {'kids': kids})
        return redirect('list_kids')
