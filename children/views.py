from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from teacher.models import Employee
from django.contrib.messages.views import SuccessMessageMixin
from .forms import KidAddForm, PaymentPlanForm
from .models import Kid, Groups, PaymentPlan, Meals
from parent.models import ParentA
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


class MealDeleteView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request, pk):
        raise PermissionDenied

    def post(self, request, pk):
        meal = get_object_or_404(Meals, id=int(pk))
        director = Director.objects.get(user=request.user.id)
        if meal.principal == director:
            for kid in meal.kid_set.filter(is_active=True):
                kid.kid_meals = None
                kid.save()
            meal.delete()
            messages.success(request,
                             f'Popprawnie usunieto posilek {meal}')
            return redirect('list_meals')
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


class KidsListView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.get_user_permissions() == {'director.is_director'}:
            kids = Director.objects.get(user=request.user.id).kid_set.filter(is_active=True)
        elif request.user.get_user_permissions() == {'teacher.is_teacher'}:
            groups = Employee.objects.get(user=request.user.id).group.filter(is_active=True)
            kids = []
            for group in groups:
                kids.append(group.kid_set.filter(is_active=True))
        elif request.user.get_user_permissions() == {'parent.is_parent'}:
            kids = ParentA.objects.get(user=request.user.id).kids.filter(is_active=True)
        else:
            raise PermissionDenied
        paginator = Paginator(kids, 10)
        page = request.GET.get('page')
        page_obj = paginator.get_page(page)
        return render(request, 'kids-list.html', {'page_obj': page_obj})

    def post(self, request):
        search = request.POST.get('search')
        if search:
            if request.user.get_user_permissions() == {'director.is_director'}:
                kids = Director.objects.get(user=request.user.id).kid_set.filter(first_name__icontains=search).filter(
                    is_active=True)
            elif request.user.get_user_permissions() == {'teacher.is_teacher'}:
                groups = Employee.objects.get(user=request.user.id).group.filter(is_active=True)
                kids = []
                for group in groups:
                    kids.append(group.kid_set.filter(first_name__icontains=search).filter(is_active=True))
            else:
                raise PermissionDenied

            paginator = Paginator(kids, 10)
            page = request.GET.get('page')
            page_obj = paginator.get_page(page)
            return render(request, 'kids-list.html', {'page_obj': page_obj})
        return redirect('list_kids')


class DetailsKidView(LoginRequiredMixin, View):

    def get(self, request, pk):
        kid = Kid.objects.filter(id=int(pk)).filter(is_active=True).first()
        if kid:
            meals = None
            if kid.kid_meals.is_active == True:
                meals = kid.kid_meals

            if request.user.get_user_permissions() == {'director.is_director'}:
                if kid.principal.user.email == request.user.email:
                    return render(request, 'kid-details.html', {'kid': kid, 'meals': meals})
            elif request.user.get_user_permissions() == {'teacher.is_teacher'}:
                teachers = kid.group.filter(is_active=True).first().employee_set.values_list('user', flat=True)
                if request.user in teachers:
                    return render(request, 'kid-details.html', {'kid': kid, 'meals': meals})
            elif request.user.get_user_permissions() == {'parent.is_parent'}:
                parents = kid.parenta_set.values_list('user__email', flat=True)
                if request.user.email in parents:
                    return render(request, 'kid-details.html', {'kid': kid, 'meals': meals})
        raise PermissionDenied


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
        try:
            if self.request.user == kid.principal.user:
                if kid.is_active == True:
                    return True
        except Exception:
            return False
        return False


class KidDeleteView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request, pk):
        raise PermissionDenied

    def post(self, request, pk):
        kid = get_object_or_404(Kid, id=int(pk))
        director = Director.objects.get(user=request.user.id)
        if kid.principal == director:
            kid.is_active = False
            kid.save()
            messages.success(request,
                             f'Popprawnie usunieto dziecko {kid}')
            return redirect('list_kids')
        raise PermissionDenied
