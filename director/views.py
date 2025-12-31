from django.contrib import messages
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, UpdateView

from .models import ContactModel, Director, MealPhotos, GroupPhotos
from .forms import ContactAddForm, DirectorUpdateForm
from teacher.models import Employee
from parent.models import ParentA
from groups.models import Groups
from children.models import Kid
from django.core.exceptions import PermissionDenied
from itertools import chain
from operator import attrgetter
from blog.views import get_active_context


class PhotosListView(LoginRequiredMixin, View):

    def get(self, request):
        role, profile_id, k_id = get_active_context(request)

        # Weryfikacja roli
        if role != 'director':
            raise PermissionDenied

        # Filtrujemy zdjęcia po kindergarten_id zamiast po profilu dyrektora
        # Używamy managera for_kindergarten lub bezpośrednio pola kindergarten_id
        group_photos = GroupPhotos.objects.filter(kindergarten_id=k_id, is_active=True)
        meal_photos = MealPhotos.objects.filter(kindergarten_id=k_id, is_active=True)

        # Łączenie QuerySetów i sortowanie po dacie utworzenia
        list_obj = sorted(
            chain(group_photos, meal_photos),
            key=attrgetter('date_created'),
            reverse=True
        )

        # Paginacja
        paginator = Paginator(list_obj, 10)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        return render(request, 'photos-list.html', {'page_obj': page_obj})


class PhotosAddView(LoginRequiredMixin, View):
    # Rezygnujemy ze statycznego permission_required na rzecz kontekstu sesji
    def get(self, request):
        role, profile_id, k_id = get_active_context(request)
        if role != 'director':
            raise PermissionDenied
        return render(request, 'photo-add.html')

    def post(self, request):
        # Pobieramy k_id z sesji użytkownika
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied

        photo_type = request.POST.get('type')
        file = request.FILES.get('file')
        name = request.POST.get('name')

        # Walidacja pól
        if not photo_type:
            messages.error(request, 'Wybierz typ ikonki')
            return redirect('photo_add')
        elif not file:
            messages.error(request, 'Wybierz plik')
            return redirect('photo_add')
        elif not name:
            messages.error(request, 'Nazwa jest wymagana')
            return redirect('photo_add')

        # Zapis do bazy z uwzględnieniem kindergarten_id zamiast principal
        if photo_type == 'group':
            GroupPhotos.objects.create(
                group_photos=file,
                kindergarten_id=k_id,
                name=name
            )
        elif photo_type == 'meal':
            MealPhotos.objects.create(
                meal_photos=file,
                kindergarten_id=k_id,
                name=name
            )

        messages.success(request, 'Poprawnie dodano ikonkę do placówki')
        return redirect('photos_list')


class PhotoDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        raise PermissionDenied

    def post(self, request, pk):
        # Pobieramy kontekst placówki z sesji
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied

        photo_type = request.POST.get("delete") # '1' dla grup, '2' dla posiłków

        try:
            if photo_type == '1':
                # Szukamy zdjęcia w ramach aktywnej placówki
                photo = get_object_or_404(GroupPhotos, id=int(pk), kindergarten_id=k_id, is_active=True)

                # Rozłączamy zdjęcie z grupami przed dezaktywacją
                groups = photo.groups_set.all()
                for group in groups:
                    group.photo = None
                    group.save()

                photo.is_active = False
                photo.save()
                messages.success(request, f'Poprawnie usunięto ikonę grupy: {photo.name}')

            elif photo_type == '2':
                # Szukamy zdjęcia posiłku w ramach aktywnej placówki
                photo = get_object_or_404(MealPhotos, id=int(pk), kindergarten_id=k_id, is_active=True)

                # Rozłączamy zdjęcie z posiłkami
                meals = photo.meals_set.all()
                for meal in meals:
                    meal.photo = None
                    meal.save()

                photo.is_active = False
                photo.save()
                messages.success(request, f'Poprawnie usunięto ikonę posiłku: {photo.name}')

            else:
                messages.error(request, "Nieprawidłowy typ obiektu do usunięcia.")

        except (ValueError, TypeError):
            messages.error(request, "Wystąpił błąd podczas przetwarzania żądania.")

        return redirect('photos_list')


class DirectorProfileView(LoginRequiredMixin, View):
    def get(self, request, pk):
        # Pobieramy k_id z sesji (aktualnie wybrane przedszkole)
        role, profile_id, k_id = get_active_context(request)

        # Pobieramy profil dyrektora, który chcemy wyświetlić
        # (Weryfikujemy, czy ten dyrektor w ogóle należy do tej samej placówki co my)
        director = get_object_or_404(Director, id=pk, kindergarten_id=k_id)

        # Logika uprawnień oparta na rolach z sesji
        has_access = False

        if role == 'director':
            # Dyrektor zawsze widzi profil swój i innych dyrektorów w swojej placówce
            has_access = True
        elif role == 'teacher':
            # Nauczyciel widzi profil dyrektora tylko w ramach aktywnej placówki
            # (get_object_or_404 powyżej już to sprawdził przez k_id)
            has_access = True
        elif role == 'parent':
            # Rodzic widzi profil dyrektora w placówce, w której ma dziecko
            # (get_object_or_404 powyżej już to sprawdził przez k_id)
            has_access = True

        if not has_access:
            raise PermissionDenied

        # Pobieramy dane PLACÓWKI, a nie konkretnego dyrektora
        # Dzięki temu lista będzie spójna dla wszystkich dyrektorów w tym przedszkolu
        groups = Groups.objects.for_kindergarten(k_id).filter(is_active=True)
        kids = Kid.objects.for_kindergarten(k_id).filter(is_active=True)

        return render(request, 'director-profile.html', {
            'director': director,
            'groups': groups,
            'kids': kids
        })


class DirectorUpdateView(LoginRequiredMixin, View):
    # Rezygnujemy ze statycznego uprawnienia na rzecz weryfikacji roli w sesji
    def get(self, request):
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied

        # Pobieramy konkretny profil dyrektora przypisany do tej sesji
        director = get_object_or_404(Director, id=profile_id, kindergarten_id=k_id)

        form = DirectorUpdateForm(instance=director)
        return render(request, 'director-update.html', {'form': form})

    def post(self, request):
        role, profile_id, k_id = get_active_context(request)

        if role != 'director':
            raise PermissionDenied

        # Pobieramy profil, upewniając się, że należy do aktywnej placówki
        director = get_object_or_404(Director, id=profile_id, kindergarten_id=k_id)

        form = DirectorUpdateForm(request.POST, instance=director)
        if form.is_valid():
            form.save()
            messages.success(request, 'Poprawnie zmieniono dane profilu dyrektora')
            # Przekierowujemy do profilu, podając ID
            return redirect('director_profile', pk=director.id)

        messages.error(request, f'Wystąpił błąd: {form.errors}')
        return redirect('director_update')


class ContactView(LoginRequiredMixin, View):
    def get(self, request):
        role, profile_id, k_id = get_active_context(request)
        context = {'active_role': role}

        # 1. Pobieranie danych kontaktowych placówki
        # Szukamy kontaktu przypisanego bezpośrednio do tej placówki
        contact = ContactModel.objects.filter(kindergarten_id=k_id).first()
        context['contact'] = contact

        # 2. Logika wyświetlania osób w kontakcie zależna od ROLI w sesji
        if role == 'director':
            # Dyrektor widzi wszystkich pracowników swojej placówki
            teachers_list = Employee.objects.filter(kindergarten_id=k_id, is_active=True).order_by('last_name')
            # Dyrektor widzi innych dyrektorów w tej samej placówce
            principals_list = Director.objects.filter(kindergarten_id=k_id).exclude(id=profile_id)
            context['principals'] = principals_list

        elif role == 'teacher':
            # Nauczyciel widzi dyrektorów swojej placówki
            principals_list = Director.objects.filter(kindergarten_id=k_id).order_by('last_name')
            p_paginator = Paginator(principals_list, 5)
            context['principals'] = p_paginator.get_page(request.GET.get('p_page'))

            # Nauczyciel może widzieć innych nauczycieli z tej samej placówki
            teachers_list = Employee.objects.filter(kindergarten_id=k_id, is_active=True).exclude(id=profile_id).order_by('last_name')

        elif role == 'parent':
            # Rodzic widzi dyrektorów placówki
            principals_list = Director.objects.filter(kindergarten_id=k_id).order_by('last_name')
            context['principals'] = principals_list

            # Rodzic widzi nauczycieli swoich dzieci (z grup, do których należą dzieci)
            parent = get_object_or_404(ParentA, id=profile_id)
            kids_groups = parent.kids.filter(kindergarten_id=k_id, is_active=True).values_list('group', flat=True)
            teachers_list = Employee.objects.filter(group__in=kids_groups, is_active=True).order_by('last_name')

        # Wspólna paginacja dla listy nauczycieli (zależnie od tego, co wyfiltrowano wyżej)
        if 'teachers_list' in locals():
            t_paginator = Paginator(teachers_list, 10)
            context['teachers'] = t_paginator.get_page(request.GET.get('t_page'))

        return render(request, 'contact.html', context)


class ContactUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ContactModel
    template_name = 'contact-update.html'
    form_class = ContactAddForm
    success_url = reverse_lazy('contact')
    success_message = "Dane kontaktowe placówki zostały zaktualizowane."

    def get_object(self, queryset=None):
        """Zapewnia, że dyrektor edytuje tylko kontakt swojej aktywnej placówki."""
        role, profile_id, k_id = get_active_context(self.request)

        if role != 'director':
            raise PermissionDenied

        # Pobieramy kontakt bezpośrednio przez kindergarten_id z sesji
        # To gwarantuje, że dyrektor nie "podglądnie" kontaktu innej placówki przez PK w URL
        contact = get_object_or_404(ContactModel, kindergarten_id=k_id)
        return contact

    def get_form_kwargs(self):
        """Przekazuje ID placówki do formularza dla poprawnej inicjalizacji."""
        kwargs = super().get_form_kwargs()
        role, profile_id, k_id = get_active_context(self.request)
        kwargs['active_principal_id'] = k_id
        return kwargs

    def form_valid(self, form):
        role, profile_id, k_id = get_active_context(self.request)
        contact = form.save(commit=False)

        # Nazwa przedszkola jest aktualizowana w metodzie save() formularza,
        # którą wcześniej przygotowaliśmy, ale tutaj upewniamy się, że relacja jest zachowana.
        if not contact.kindergarten_id:
            contact.kindergarten_id = k_id

        contact.save()
        return super().form_valid(form)


class GiveDirectorPermissions(LoginRequiredMixin, View):
    def get(self, request):
        role, profile_id, k_id = get_active_context(request)
        if role != 'director':
            raise PermissionDenied

        # Pobieramy pracowników TYLKO z tej konkretnej placówki
        employees = Employee.objects.filter(kindergarten_id=k_id, is_active=True).order_by('-id')

        paginator = Paginator(employees, 10)
        page_obj = paginator.get_page(request.GET.get('page'))
        return render(request, 'give-director-permission.html', context={'page_obj': page_obj})

    def post(self, request):
        role, profile_id, k_id = get_active_context(request)
        if role != 'director':
            raise PermissionDenied

        action = request.POST.get('action')
        search = request.POST.get('search')

        # 1. Obsługa wyszukiwania w ramach placówki
        if action == 'search' or search:
            employees = Employee.objects.filter(
                kindergarten_id=k_id,
                user__email__icontains=search
            ).order_by('-id')

            paginator = Paginator(employees, 10)
            page_obj = paginator.get_page(request.GET.get('page'))
            return render(request, 'give-director-permission.html', context={'page_obj': page_obj})

        # 2. Obsługa nadawania uprawnień
        if action == 'grant':
            pk_list = request.POST.getlist('pk')

            if pk_list:
                # Pobieramy techniczne uprawnienie
                content_type = ContentType.objects.get_for_model(Director)
                permission = Permission.objects.get(content_type=content_type, codename='is_director')

                # Pobieramy wybranych pracowników tej placówki
                employees = Employee.objects.filter(id__in=pk_list, kindergarten_id=k_id)

                for employee in employees:
                    # Dodajemy uprawnienie techniczne do Usera
                    employee.user.user_permissions.add(permission)

                    # TWORZYMY PROFIL DYREKTORA DLA TEJ SAMEJ PLACÓWKI
                    # To kluczowe: nowy dyrektor musi być przypisany do k_id
                    new_director, created = Director.objects.get_or_create(
                        user=employee.user,
                        kindergarten_id=k_id,
                        defaults={
                            'first_name': employee.first_name,
                            'last_name': employee.last_name,
                            'gender': employee.gender
                        }
                    )

                messages.success(request, f'Pomyślnie nadano uprawnienia dyrektorskie dla {employees.count()} osób w tej placówce.')
            else:
                messages.error(request, 'Nie wybrano żadnego pracownika.')

        return redirect('give-permissions')
