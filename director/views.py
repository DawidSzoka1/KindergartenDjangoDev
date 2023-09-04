from django.contrib import messages
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


class DirectorProfileView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        director = get_object_or_404(Director, user=request.user.id)
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
        if user.get_all_permissions() == {'director.is_director'}:
            contact = ContactModel.objects.get(director=Director.objects.get(user=user.id))
        elif user.get_all_permissions() == {'teacher.is_teacher'}:
            contact = ContactModel.objects.get(director=Employee.objects.get(user=user.id).principal.all().first())
        else:
            contact = ContactModel.objects.get(director=ParentA.objects.get(user=user.id).principal.all().first())

        return render(request, 'contact.html', {'contact': contact})


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
