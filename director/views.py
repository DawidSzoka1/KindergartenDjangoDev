from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import PermissionRequiredMixin
from .models import ContactModel, Director
from teacher.models import Employee
from parent.models import ParentA


class DirectorProfileView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        return render(request, 'director-profile.html')


class Contact(PermissionRequiredMixin, View):
    def get(self, request):
        user = request.user
        if user.user_permissions == 'Is the director of kindergarten':
            contact = ContactModel.objects.get(director=Director.objects.get(user=user.id))
        elif user.user_permissions == 'Is the teacher of some group':
            contact = ContactModel.objects.get(director=Employee.objects.get(user=user.id).principal.all().first())
        else:
            contact = ContactModel.objects.get(director=ParentA.objects.get(user=user.id).principal.all().first())

        return render(request, 'contact.html', {'contact': contact})

