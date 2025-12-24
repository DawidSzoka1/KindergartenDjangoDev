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
from django.core.exceptions import PermissionDenied
from itertools import chain
from operator import attrgetter


class PhotosListView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        group_photos = GroupPhotos.objects.filter(principal=request.user.director).filter(is_active=True)
        meal_photos = MealPhotos.objects.filter(principal=request.user.director).filter(is_active=True)
        list_obj = sorted(
            chain(group_photos, meal_photos),
            key=attrgetter('date_created'),
            reverse=True

        )

        paginator = Paginator(list_obj, 10)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        return render(request, 'photos-list.html', {'page_obj': page_obj})


class PhotosAddView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        return render(request, 'photo-add.html')

    def post(self, request):
        photo_type = request.POST.get('type')
        file = request.FILES.get('file')
        name = request.POST.get('name')
        if not photo_type:
            messages.error(request, 'Wybierz typ iconki')
            return redirect('photo_add')
        elif not file:
            messages.error(request, 'Wybierz jakis plik')
            return redirect('photo_add')
        elif not name:
            messages.error(request, 'Nazwa jest wymagana')
            return redirect('photo_add')
        if photo_type == 'group':
            GroupPhotos.objects.create(group_photos=file, principal=request.user.director, name=name)
        elif photo_type == 'meal':
            MealPhotos.objects.create(meal_photos=file, principal=request.user.director, name=name)
        messages.success(request, 'Poprawnie dodano ikonkę')
        return redirect('photos_list')


class PhotoDeleteView(PermissionRequiredMixin, View):
    permission_required = 'director.is_director'

    def get(self, request, pk):
        raise PermissionDenied

    def post(self, request, pk):
        type = int(request.POST.get("delete"))
        director = get_object_or_404(Director, user=request.user.id)
        if type == 1:
            photo = get_object_or_404(GroupPhotos, id=int(pk))
            if photo in director.groupphotos_set.filter(is_active=True):
                photo.is_active = False
                groups = photo.groups_set.all()
                for group in groups:
                    group.photo = None
                    group.save()
                photo.save()
                messages.success(request, f'Poprawnie usunieto zdjecie {photo.name}')
            else:
                raise PermissionDenied

        elif type == 2:
            photo = get_object_or_404(MealPhotos, id=int(pk))
            if photo in director.mealphotos_set.filter(is_active=True):
                photo.is_active = False
                meals = photo.meals_set.all()
                for meal in meals:
                    meal.photo = None
                    meal.save()
                photo.save()
                messages.success(request, f'Poprawnie usunieto zdjecie {photo.name}')
            else:
                raise PermissionDenied
        else:
            messages.error(request, "Cos poszło nie tak")
        return redirect('photos_list')


class DirectorProfileView(LoginRequiredMixin, View):
    def get(self, request, pk):
        director = get_object_or_404(Director, id=pk)
        user = request.user

        # Logika uprawnień: Sprawdzamy czy użytkownik ma prawo widzieć ten profil
        has_access = False

        if user.get_all_permissions() == {'director.is_director'}:
            # Dyrektor widzi swój profil (i opcjonalnie innych dyrektorów w tej samej placówce)
            has_access = True
        elif user.get_all_permissions() == {'teacher.is_teacher'}:
            # Nauczyciel widzi profil swojego dyrektora
            employee = get_object_or_404(Employee, user=user)
            if director in employee.principal.all():
                has_access = True
        else:
            # Rodzic widzi profil dyrektora swojej placówki
            parent = get_object_or_404(ParentA, user=user)
            if director in parent.principal.all():
                has_access = True

        if not has_access:
            raise PermissionDenied

        groups = director.groups_set.filter(is_active=True)
        kids = director.kid_set.filter(is_active=True)
        return render(request, 'director-profile.html', {'director': director, 'groups': groups, 'kids': kids})


class DirectorUpdateView(PermissionRequiredMixin, View):
    permission_required = 'director.is_director'

    def get(self, request):
        director = Director.objects.get(user=request.user.id)
        form = DirectorUpdateForm(instance=director)
        return render(request, 'director-update.html', {'form': form})

    def post(self, request):
        director = Director.objects.get(user=request.user.id)
        form = DirectorUpdateForm(request.POST, instance=director)
        if form.is_valid():
            form.save()
            messages.success(request, 'Poprawnie zmieniono dane')
            return redirect('director_profile')
        messages.error(request, f'{form.errors}')
        return redirect('director_update')


class ContactView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        context = {}

        # Pobieranie podstawowych danych kontaktowych placówki
        if 'director.is_director' in user.get_all_permissions():
            director_obj = Director.objects.get(user=user.id)
            contact = ContactModel.objects.filter(director=director_obj).first()
        elif 'teacher.is_teacher' in user.get_all_permissions():
            employee = Employee.objects.get(user=user.id)
            director_obj = employee.principal.all().first()
            contact = ContactModel.objects.filter(director=director_obj).first()

            # Paginacja dyrektorów dla nauczyciela
            principals_list = employee.principal.all().order_by('last_name')
            p_paginator = Paginator(principals_list, 5)
            context['principals'] = p_paginator.get_page(request.GET.get('p_page'))
        else:
            parent = ParentA.objects.get(user=user.id)
            director_obj = parent.principal.all().first()
            contact = ContactModel.objects.filter(director=director_obj).first()

            # Paginacja dyrektorów dla rodzica
            principals_list = parent.principal.all().order_by('last_name')
            p_paginator = Paginator(principals_list, 3)
            context['principals'] = p_paginator.get_page(request.GET.get('p_page'))

            # Paginacja nauczycieli dla rodzica
            kids_groups = parent.kids.filter(is_active=True).values_list('group', flat=True)
            teachers_list = Employee.objects.filter(group__in=kids_groups, is_active=True).order_by('last_name')
            t_paginator = Paginator(teachers_list, 5)
            context['teachers'] = t_paginator.get_page(request.GET.get('t_page'))

        context['contact'] = contact
        return render(request, 'contact.html', context)


class ContactUpdateView(PermissionRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    permission_required = "director.is_director"
    model = ContactModel
    template_name = 'contact-update.html'
    form_class = ContactAddForm
    success_url = reverse_lazy('contact')
    success_message = "Dane kontaktowe zmieniono poprawnie"

    def form_valid(self, form):
        form.instance.save()
        return super().form_valid(form)

    def test_func(self):
        contact = self.get_object()
        try:
            if self.request.user == contact.director.user:
                return True
        except Exception:
            return False
        return False


class GiveDirectorPermissions(PermissionRequiredMixin, LoginRequiredMixin, View):
    permission_required = 'director.is_director'

    def get(self, request):
        # Pobieramy tylko tych pracowników, którzy są przypisani do dyrektora
        employees = Employee.objects.filter(principal=Director.objects.get(user=request.user)).order_by('-id')
        paginator = Paginator(employees, 10)
        page = request.GET.get('page')
        page_obj = paginator.get_page(page)
        return render(request, 'give-director-permission.html', context={'page_obj': page_obj})

    def post(self, request):
        action = request.POST.get('action')
        search = request.POST.get('search')
        director = Director.objects.get(user=request.user)

        # Obsługa wyszukiwania
        if action == 'search' or search:
            employees = Employee.objects.filter(principal=director).filter(
                user__email__icontains=search).order_by('-id')
            paginator = Paginator(employees, 10)
            page = request.GET.get('page')
            page_obj = paginator.get_page(page)
            return render(request, 'give-director-permission.html', context={'page_obj': page_obj})

        # Obsługa nadawania uprawnień
        if action == 'grant':
            content_type = ContentType.objects.get_for_model(Director)
            permission = Permission.objects.get(content_type=content_type, codename='is_director')
            pk_list = request.POST.getlist('pk')

            if pk_list:
                employees = Employee.objects.filter(id__in=pk_list)
                for employee in employees:
                    employee.user.user_permissions.add(permission)
                messages.success(request, f'Pomyślnie nadano uprawnienia dla {employees.count()} pracowników.')
            else:
                messages.error(request, 'Nie wybrano żadnego pracownika.')

        return redirect('give-permissions')
