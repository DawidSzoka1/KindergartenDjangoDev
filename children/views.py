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
            # NOWA LOGIKA DLA RODZICA
            parent = get_object_or_404(ParentA, user=request.user)
            kids = parent.kids.filter(is_active=True)
            groups_count = kids.values('group').distinct().count()

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
            elif request.user.get_user_permissions() == {'parent.is_parent'}:
                # NOWA LOGIKA DLA RODZICA
                parent = get_object_or_404(ParentA, user=request.user.id)
                kids = parent.kids.filter(is_active=True)
                groups_count = kids.values('group').distinct().count()
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


from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from .forms import KidUpdateForm

class ChangeKidInfoView(PermissionRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    permission_required = "director.is_director"
    model = Kid
    template_name = 'kid-update-info.html'
    form_class = KidUpdateForm
    success_message = "Profil dziecka został zaktualizowany!"

    def get_success_url(self):
        return reverse_lazy('kid_details', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self, **kwargs):
        """Przekazuje current_user do formularza"""
        kwargs = super(ChangeKidInfoView, self).get_form_kwargs()
        kwargs.update({'current_user': self.request.user})
        return kwargs

    def get_form(self, form_class=None):
        form = super(ChangeKidInfoView, self).get_form(form_class)
        form.fields['end'].required = False

        # Usuwamy pole parents z walidacji formularza, bo obsługujemy je ręcznie w form_valid
        if 'parents' in form.fields:
            del form.fields['parents']
        return form

    # --- TO JEST METODA, KTÓREJ BRAKOWAŁO ---
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pobieramy wszystkich rodziców przypisanych do tego dyrektora,
        # żeby wypełnić <select> w HTML
        context['all_parents'] = ParentA.objects.filter(principal__user=self.request.user)
        return context
    # -----------------------------------------

    def form_valid(self, form):
        kid = form.save(commit=False)

        # Umowa na czas nieokreślony
        if self.request.POST.get('indefinite'):
            kid.end = None

        kid.save()

        # Obsługa rodziców (wielu, z inputa hidden)
        parents_input = self.request.POST.get('parents', '')

        if parents_input:
            # Rozbijamy string "1,2,5" na listę liczb
            parent_ids = [int(pid) for pid in parents_input.split(',') if pid.strip().isdigit()]

            # Pobieramy rodziców z bazy (tylko należących do tego dyrektora)
            parents = ParentA.objects.filter(
                id__in=parent_ids,
                principal__user=self.request.user
            )
            kid.parenta_set.set(parents)
        else:
            # Jeśli lista pusta, usuwamy powiązania
            kid.parenta_set.clear()

        kid.save()
        return super().form_valid(form)

    def test_func(self):
        kid = self.get_object()
        try:
            return self.request.user == kid.principal.user and kid.is_active
        except Exception:
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
        kid = get_object_or_404(Kid, id=int(pk))
        user_perms = request.user.get_all_permissions()

        # Logika sprawdzania dostępu
        can_access = False

        if 'director.is_director' in user_perms:
            # Sprawdzenie czy dziecko należy do placówki dyrektora
            if kid.principal.user == request.user:
                can_access = True

        elif 'teacher.is_teacher' in user_perms:
            # Sprawdzenie czy nauczyciel uczy w grupie tego dziecka
            if kid.group and request.user.employee in kid.group.employee_set.all():
                can_access = True

        elif 'parent.is_parent' in user_perms:
            # Sprawdzenie czy to rodzic tego konkretnego dziecka
            if request.user.parenta in kid.parenta_set.all():
                can_access = True

        if not can_access:
            raise PermissionDenied

        parents = kid.parenta_set.all().select_related('user')
        return render(request, 'kid-parent-info.html', {
            'kid': kid,
            'parents': parents,
            'today': timezone.now()
        })

    def post(self, request, pk):
        from django.db import transaction
        """Obsługa odłączania rodzica od dziecka z weryfikacją placówki"""
        user = request.user

        # 1. Sprawdzenie podstawowych uprawnień dyrektora
        if not user.has_perm('director.is_director'):
            raise PermissionDenied

        # 2. Pobranie dziecka i weryfikacja przynależności do placówki
        kid = get_object_or_404(Kid, id=pk)

        # Sprawdzamy czy dyrektor przypisany do dziecka to ten sam, który jest zalogowany
        if kid.principal.user != user:
            messages.error(request, "Nie masz uprawnień do zarządzania tym dzieckiem.")
            return redirect('list_kids') # Lub inna strona zbiorcza

        parent_id = request.POST.get('parent_id')
        parent = get_object_or_404(ParentA, id=parent_id)

        # 3. Bezpieczne odłączenie relacji
        try:
            with transaction.atomic():
                # Usuwamy powiązanie w tabeli ManyToMany
                kid.parenta_set.remove(parent)
                messages.success(request, f"Opiekun {parent.first_name} został odłączony od dziecka {kid.first_name}.")
        except Exception as e:
            messages.error(request, "Wystąpił błąd podczas odłączania opiekuna.")

        return redirect('kid_parent', pk=kid.id)
