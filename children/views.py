from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from teacher.models import Employee
from groups.models import Groups
from django.contrib.messages.views import SuccessMessageMixin
from .forms import KidAddForm, KidUpdateForm
from .models import Kid
from django.utils import timezone
from parent.models import ParentA
from django.core.exceptions import PermissionDenied
from director.models import Director
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin, LoginRequiredMixin
from django.views.generic import (
    CreateView,
    UpdateView,
)


# Create your views here.


class AddKidView(PermissionRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, CreateView):
    permission_required = "director.is_director"
    model = Kid
    template_name = 'kid-add.html'
    form_class = KidAddForm
    success_url = reverse_lazy('list_kids')
    success_message = "Dodano poprawnie dziecko"

    def get_initial(self):
        initial = super(AddKidView, self).get_initial()
        initial = initial.copy()
        initial['principal'] = Director.objects.get(user=self.request.user.id)
        return initial

    def get_form_kwargs(self, **kwargs):
        """ Passes the request object to the form class.
         This is necessary to only display members that belong to a given user"""

        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['group'].required = False
        form.fields['payment_plan'].required = False
        form.fields['kid_meals'].required = False
        form.fields['end'].required = False
        return form

    def form_valid(self, form):
        if self.request.POST.get('indefinite'):
            form.instance.end = None

        kid = form.save(commit=False)  # pobieramy instancję
        kid.save()  # zapisujemy w bazie

        messages.success(self.request, self.success_message)
        return super().form_valid(form)

    def test_func(self):
        director = get_object_or_404(Director, user=self.request.user.id)
        if director.groups_set.filter(is_active=True):
            if director.meals_set.filter(is_active=True):
                if director.paymentplan_set.filter(is_active=True):
                    return True
        return False

    def handle_no_permission(self):
        director = get_object_or_404(Director, user=self.request.user.id)
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
            kids = get_object_or_404(Director, user=request.user.id).kid_set.filter(is_active=True).order_by('-id')
            groups_count = Groups.objects.filter(principal=request.user.id, is_active=True).count()
        elif request.user.get_user_permissions() == {'teacher.is_teacher'}:
            groups = get_object_or_404(Employee, user=request.user.id).group
            groups_count = groups.filter(is_active=True).count()
            if groups.is_active:
                kids = groups.kid_set.filter(is_active=True).order_by('-id')
            else:
                kids = None

        elif request.user.get_user_permissions() == {'parent.is_parent'}:
            kids = get_object_or_404(ParentA, user=request.user.id).kids.filter(is_active=True).order_by('-id')
            groups_count = get_object_or_404(ParentA, user=request.user.id).kids.group.filter(is_active=True).count()
        else:
            raise PermissionDenied

        paginator = Paginator(kids, 10)
        kids_count = kids.count()
        avg = 0
        for kid in kids:
            print(kid.date_of_birth)
            avg += kid.years_old()
        avg /= kids_count
        page = request.GET.get('page')
        page_obj = paginator.get_page(page)
        month = int(timezone.now().month)
        year = int(timezone.now().year)

        return render(request, 'kids-list.html',
                      {'page_obj': page_obj, 'month': month, 'year': year, 'total_kids': kids_count,
                       'groups_count': groups_count, 'avg_age': avg})

    def post(self, request):
        search = request.POST.get('search')
        if search:
            if request.user.get_user_permissions() == {'director.is_director'}:
                kids = get_object_or_404(Director, user=request.user.id).kid_set.filter(
                    first_name__icontains=search).filter(
                    is_active=True).order_by('-id')
                groups_count = Groups.objects.filter(principal=request.user.id, is_active=True).count()
            elif request.user.get_user_permissions() == {'teacher.is_teacher'}:
                group = get_object_or_404(Employee, user=request.user.id).group
                kids = group.kid_set.filter(first_name__icontains=search).filter(is_active=True).order_by('-id')
                groups_count = groups.filter(is_active=True).count()
            else:
                raise PermissionDenied
            kids_count = kids.count()
            avg = 0
            for kid in kids:
                print(kid.date_of_birth)
                avg += kid.years_old()
            avg /= kids_count if kids_count > 0 else 1
            paginator = Paginator(kids, 10)
            page = request.GET.get('page')
            page_obj = paginator.get_page(page)
            month = int(timezone.now().month)
            year = int(timezone.now().year)
            return render(request, 'kids-list.html',
                          {'page_obj': page_obj, 'month': month, 'year': year, 'total_kids': kids_count,
                           'groups_count': groups_count, 'avg_age': avg})
        return redirect('list_kids')


class DetailsKidView(LoginRequiredMixin, View):

    def get(self, request, pk):
        kid = Kid.objects.filter(id=int(pk)).filter(is_active=True).first()
        if kid:
            meals = None
            if kid.kid_meals:
                if kid.kid_meals.is_active == True:
                    meals = kid.kid_meals

            if request.user.get_user_permissions() == {'director.is_director'}:
                if kid.principal.user.email == request.user.email:
                    return render(request, 'kid-details.html', {'kid': kid, 'meals': meals})
            elif request.user.get_user_permissions() == {'teacher.is_teacher'}:
                teachers = kid.group.employee_set.values_list('user__email', flat=True)
                if request.user.email in teachers:
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
    form_class = KidUpdateForm
    success_message = "Profil dziecka został zaktualizowany!"

    def get_success_url(self):
        return reverse_lazy('kid_details', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self, **kwargs):
        """ Passes the request object to the form class.
         This is necessary to only display members that belong to a given user"""

        kwargs = super(ChangeKidInfoView, self).get_form_kwargs()
        kwargs.update({'current_user': self.request.user})
        return kwargs

    def form_valid(self, form):
        kid = form.save(commit=False)

        # Umowa na czas nieokreślony
        if self.request.POST.get('indefinite'):
            kid.end = None
        kid.save()
        selected_parents = form.cleaned_data.get('parents', [])
        kid.parenta_set.set(selected_parents)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Wszyscy rodzice należący do tego dyrektora
        context['all_parents'] = ParentA.objects.filter(
            principal__user=self.request.user
        ).select_related('user')
        return context

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
        director = get_object_or_404(Director, user=request.user.id)
        if kid.principal == director:
            kid.is_active = False
            kid.save()
            messages.success(request,
                             f'Popprawnie usunieto dziecko {kid}')
            return redirect('list_kids')
        raise PermissionDenied


class KidParentInfoView(LoginRequiredMixin, View):
    def get(self, request, pk):
        user = request.user.get_user_permissions()
        kid = get_object_or_404(Kid, id=int(pk))
        parents = None
        if user == {'director.is_director'}:
            if kid.principal.user.email == request.user.email:
                parents = kid.parenta_set.all()

        elif user == {'teacher.is_teacher'}:
            if request.user.email in kid.group.employee_set.values_list('user__email', flat=True):
                parents = kid.parenta_set.all()

        elif user == {'parent.is_parent'}:
            if request.user.email in kid.parenta_set.values_list('user__email', flat=True):
                parents = kid.parenta_set.all()

        if parents:
            return render(request, 'kid-parent-info.html', {'kid': kid, 'parents': parents})
        raise PermissionDenied
