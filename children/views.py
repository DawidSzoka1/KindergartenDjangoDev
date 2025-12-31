from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from teacher.models import Employee
from groups.models import Groups
from meals.models import Meals
from payments_plans.models import PaymentPlan
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
from blog.views import get_active_context


# Create your views here.


class AddKidView(UserPassesTestMixin, SuccessMessageMixin, CreateView):
    model = Kid
    template_name = 'kid-add.html'
    form_class = KidAddForm
    success_url = reverse_lazy('list_kids')
    success_message = "Dodano poprawnie dziecko"

    def get_initial(self):
        initial = super(AddKidView, self).get_initial()
        role, profile_id, principal_id = get_active_context(self.request)
        initial = initial.copy()
        initial['principal'] = get_object_or_404(Director, id=principal_id)
        return initial

    def get_form_kwargs(self, **kwargs):
        """ Passes the request object to the form class.
         This is necessary to only display members that belong to a given user"""

        kwargs = super().get_form_kwargs()
        role, profile_id, k_id = get_active_context(self.request)
        kwargs.update({
            'current_user': self.request.user,
            'active_principal_id': k_id  # Przekazujemy ID przedszkola do formy
        })
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['group'].required = False
        form.fields['payment_plan'].required = False
        form.fields['kid_meals'].required = False
        form.fields['end'].required = False
        return form

    def form_valid(self, form):
        # 1. Obsługa daty na czas nieokreślony
        if self.request.POST.get('indefinite'):
            form.instance.end = None

        # 2. Przypisanie placówki do dziecka
        role, profile_id, k_id = get_active_context(self.request)
        form.instance.kindergarten_id = k_id

        # 3. Zapis dziecka
        response = super().form_valid(form)
        kid = self.object

        # 4. PRZYPISANIE RODZICÓW
        # Pobieramy listę ID rodziców z pola 'parents' (zdefiniowanego w KidAddForm)
        selected_parents = form.cleaned_data.get('parents')
        if selected_parents:
            for parent in selected_parents:
                parent.kids.add(kid) # Zakładając, że ParentA ma kids = ManyToManyField(Kid)

        return response

    def test_func(self):
        role, profile_id, k_id = get_active_context(self.request)
        if role != 'director':
            return False
        # Sprawdzamy czy placówka ma wymagane dane bazowe
        has_groups = Groups.objects.for_kindergarten(k_id).filter(is_active=True).exists()
        has_meals = Meals.objects.for_kindergarten(k_id).filter(is_active=True).exists()
        has_plans = PaymentPlan.objects.for_kindergarten(k_id).filter(is_active=True).exists()
        return has_groups and has_meals and has_plans

    def handle_no_permission(self):
        role, profile_id, k_id = get_active_context(self.request)
        # 1. Sprawdzenie roli (bez zmian)
        if role != 'director':
            raise PermissionDenied

        # 2. Sprawdzanie zasobów w ramach całej placówki (k_id)
        # Używamy managerów for_kindergarten, aby sprawdzić czy JAKIKOLWIEK dyrektor dodał te dane
        if not Groups.objects.for_kindergarten(k_id).filter(is_active=True).exists():
            messages.error(self.request, 'W placówce nie ma jeszcze żadnej grupy. Dodaj ją najpierw.')
            return redirect('add_group')

        if not Meals.objects.for_kindergarten(k_id).filter(is_active=True).exists():
            messages.error(self.request, 'W placówce nie ma zdefiniowanych posiłków.')
            return redirect('add_meal')

        if not PaymentPlan.objects.for_kindergarten(k_id).filter(is_active=True).exists():
            messages.error(self.request, 'W placówce nie ma planów płatniczych.')
            return redirect('add_payment_plans')

        # Fallback, jeśli test_func zwrócił False z innego powodu
        return redirect('home_page')


class KidsListView(LoginRequiredMixin, View):
    def get(self, request):
        role, profile_id, k_id = get_active_context(request)
        search_query = request.GET.get('search', '')
        kids_queryset = Kid.objects.for_kindergarten(k_id).filter(is_active=True)
        if role == 'director':
            kids = kids_queryset
            groups_count = Groups.objects.for_kindergarten(k_id).filter(is_active=True).count()
        elif role == 'teacher':
            teacher = get_object_or_404(Employee, id=profile_id, user=request.user)
            group = teacher.group
            if group and group.is_active:
                kids = kids_queryset.filter(group=group).order_by('-id')
                groups_count = 1
            else:
                kids = Kid.objects.none()
                groups_count = 0
        elif role == 'parent':
            # NOWA LOGIKA DLA RODZICA
            parent = get_object_or_404(ParentA, id=profile_id, user=request.user)
            kids = parent.kids.filter(is_active=True, kindergarten_id=k_id)
            groups_count = kids.values('group').distinct().count()

        else:
            raise PermissionDenied
        if search_query:
            kids = kids.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        paginator = Paginator(kids, 10)
        kids_count = kids.count()
        avg = sum(k.years_old() for k in kids) / kids_count if kids_count > 0 else 0
        page = request.GET.get('page')
        page_obj = paginator.get_page(page)
        month = int(timezone.now().month)
        year = int(timezone.now().year)

        return render(request, 'kids-list.html',
                      {'page_obj': page_obj, 'month': month, 'year': year, 'total_kids': kids_count,
                       'groups_count': groups_count, 'avg_age': avg})

    def post(self, request):
        search = request.POST.get('search')
        # Przekierowanie do GET zapewnia poprawne działanie paginacji z filtrem wyszukiwania
        if search:
            return redirect(f"{reverse('list_kids')}?search={search}")
        return redirect('list_kids')


class DetailsKidView(LoginRequiredMixin, View):

    def get(self, request, pk):
        role, profile_id, k_id = get_active_context(request)
        kid = get_object_or_404(Kid, id=pk, kindergarten_id=k_id, is_active=True)
        if str(kid.kindergarten.id) != str(k_id):
            raise PermissionDenied
        meals = kid.kid_meals if kid.kid_meals and kid.kid_meals.is_active else None
        can_view = False
        if role == 'director':
            can_view = True
        elif role == 'teacher':
            teacher = get_object_or_404(Employee, id=profile_id, user=request.user)
            if kid.group == teacher.group:
                can_view = True
        elif role == 'parent':
            parent = get_object_or_404(ParentA, id=profile_id, user=request.user)
            if parent.kids.filter(id=kid.id).exists():
                can_view = True

        if not can_view:
            raise PermissionDenied

        return render(request, 'kid-details.html', {'kid': kid, 'meals': meals})


from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from .forms import KidUpdateForm


class ChangeKidInfoView(UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Kid
    template_name = 'kid-update-info.html'
    form_class = KidUpdateForm
    success_message = "Profil dziecka został zaktualizowany!"

    def get_success_url(self):
        return reverse_lazy('kid_details', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self, **kwargs):
        """Przekazuje current_user do formularza"""
        kwargs = super().get_form_kwargs()
        role, profile_id, k_id = get_active_context(self.request)
        kwargs.update({
            'current_user': self.request.user,
            'active_principal_id': k_id  # Przekazujemy ID przedszkola
        })
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
        role, profile_id, k_id = get_active_context(self.request)
        # Pobieramy rodziców należących do TEJ placówki
        context['all_parents'] = ParentA.objects.filter(kindergarten_id=k_id)
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
        role, profile_id, k_id = get_active_context(self.request)
        if parents_input:
            # Rozbijamy string "1,2,5" na listę liczb
            parent_ids = [int(pid) for pid in parents_input.split(',') if pid.strip().isdigit()]

            # Pobieramy rodziców z bazy (tylko należących do tego dyrektora)
            parents = ParentA.objects.filter(id__in=parent_ids, kindergarten_id=k_id)
            kid.parenta_set.set(parents)
        else:
            # Jeśli lista pusta, usuwamy powiązania
            kid.parenta_set.clear()

        kid.save()
        return super().form_valid(form)

    def test_func(self):
        role, profile_id, k_id = get_active_context(self.request)
        kid = self.get_object()
        # Sprawdzamy, czy dyrektor ma dostęp do placówki, do której należy dziecko
        return role == 'director' and kid.kindergarten_id == int(k_id)


class KidDeleteView(PermissionRequiredMixin, View):
    permission_required = 'director.is_director'

    def post(self, request, pk):
        role, profile_id, k_id = get_active_context(request)
        if role != 'director':
            raise PermissionDenied
        kid = get_object_or_404(Kid, id=pk, kindergarten_id=k_id)
        kid.is_active = False
        kid.save()

        messages.success(request, f'Poprawnie usunięto dziecko: {kid}')
        return redirect('list_kids')


class KidParentInfoView(LoginRequiredMixin, View):
    def get(self, request, pk):
        user_perms = request.user.get_all_permissions()
        role, profile_id, k_id = get_active_context(request)
        kid = get_object_or_404(Kid, id=pk, kindergarten_id=k_id)
        # Logika sprawdzania dostępu
        can_access = False

        if role == 'director':
            # Każdy dyrektor przypisany do tej placówki ma dostęp
            can_access = True

        elif role == 'teacher':
            # Sprawdzenie przez aktywny profil nauczyciela z sesji
            teacher = get_object_or_404(Employee, id=profile_id)
            if kid.group == teacher.group:
                can_access = True

        elif role == 'parent':
            # Sprawdzenie przez aktywny profil rodzica z sesji
            parent = get_object_or_404(ParentA, id=profile_id)
            if parent.kids.filter(id=kid.id).exists():
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
        role, profile_id, k_id = get_active_context(request)
        user = request.user

        # 1. Sprawdzenie podstawowych uprawnień dyrektora
        if role != 'director':
            raise PermissionDenied

        # 2. Pobranie dziecka i weryfikacja przynależności do placówki
        kid = get_object_or_404(Kid, id=pk, kindergarten_id=k_id)

        # Sprawdzamy czy dyrektor przypisany do dziecka to ten sam, który jest zalogowany
        if kid.principal.user != user:
            messages.error(request, "Nie masz uprawnień do zarządzania tym dzieckiem.")
            return redirect('list_kids')  # Lub inna strona zbiorcza

        parent_id = request.POST.get('parent_id')
        parent = get_object_or_404(ParentA, id=parent_id, kindergarten_id=k_id)

        # 3. Bezpieczne odłączenie relacji
        try:
            with transaction.atomic():
                # Usuwamy powiązanie w tabeli ManyToMany
                kid.parenta_set.remove(parent)
                messages.success(request, f"Opiekun {parent.first_name} został odłączony od dziecka {kid.first_name}.")
        except Exception as e:
            messages.error(request, "Wystąpił błąd podczas odłączania opiekuna.")

        return redirect('kid_parent', pk=kid.id)
