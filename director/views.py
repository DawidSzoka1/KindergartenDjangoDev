from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import PermissionRequiredMixin
from .models import ContactModel, Director
from teacher.models import Employee
from parent.models import ParentA


class DirectorProfileView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        director = Director.objects.get(user=self.request.user.id)
        return render(request, 'director-profile.html', {'director': director})

    def post(self, request):
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        director = Director.objects.get(user=self.request.user.id)


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
