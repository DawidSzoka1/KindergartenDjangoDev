from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import PermissionRequiredMixin
from .models import ContactModel, Director, MealPhotos, GroupPhotos
from teacher.models import Employee
from parent.models import ParentA


class PhotosListView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        group_photos = GroupPhotos.objects.filter(principal=request.user.director)
        meal_photos = MealPhotos.objects.filter(principal=request.user.director)
        return render(request, 'photos-list.html', {'group_photos': group_photos, 'meal_photos': meal_photos})


class PhotosAddView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        return render(request, 'photo-add.html', )

    def post(self, request):
        photo_type = request.POST.get('type')
        file = request.FILES.get('file')
        if file and photo_type:
            if photo_type == 'group':
                GroupPhotos.objects.create(group_photos=file, principal=request.user.director)
            if photo_type == 'meal':
                MealPhotos.objects.create(meal_photos=file, principal=request.user.director)
            messages.success(request, 'udalo sie')
            return redirect('photos_list')

        messages.error(request, 'blad')
        return redirect('photo_add')


class DirectorProfileView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        director = Director.objects.get(user=self.request.user.id)
        return render(request, 'director-profile.html', {'director': director})


class ContactView(View):
    def get(self, request):
        user = request.user
        if user.get_all_permissions() == {'director.is_director'}:
            contact = ContactModel.objects.get(director=Director.objects.get(user=user.id))
        elif user.get_all_permissions() == {'teacher.is_teacher'}:
            contact = ContactModel.objects.get(director=Employee.objects.get(user=user.id).principal.all().first())
        else:
            contact = ContactModel.objects.get(director=ParentA.objects.get(user=user.id).principal.all().first())

        return render(request, 'contact.html', {'contact': contact})


class ContactUpdateView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        contact = ContactModel.objects.get(director=Director.objects.get(user=self.request.user.id))
        return render(request, 'contact-update.html', {'contact': contact})

    def post(self, request):
        address = request.POST.get('address')
        email_address = request.POST.get('email_address')
        phone = request.POST.get('phone')
        city = request.POST.get('city')
        zip_code = request.POST.get('zip_code')
        director = Director.objects.get(user=self.request.user.id)
        if address and email_address and phone and city and zip_code:
            contact = ContactModel.objects.get(director=director)
            contact.address = address
            contact.email_address = email_address
            contact.phone = phone
            contact.city = city
            contact.zip_code = zip_code
            contact.save()
            return redirect('contact')
        messages.error(request, 'Wypełnij wszytkie pola poprawnie poprawnie')
        return redirect('contact-update')
