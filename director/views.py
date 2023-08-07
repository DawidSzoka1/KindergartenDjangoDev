from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import PermissionRequiredMixin


class DirectorProfileView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        return render(request, 'director-profile.html')
