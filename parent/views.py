from django.shortcuts import render, redirect
from django.views import View
from director.models import Director
from .forms import ParentUpdateForm, UserUpdateForm
from .models import ParentA
from django.contrib.auth.mixins import LoginRequiredMixin
# Create your views here.


class ParentProfileView(LoginRequiredMixin, View):
    def get(self, request):
        parent_logged = ParentA.objects.get(user=request.user.id)
        parent_kids = parent_logged.kid_set.all()
        return render(request, 'parent_profile.html', {'parent_logged': parent_logged, 'parent_kids': parent_kids})


class ParentProfileUpdate(LoginRequiredMixin, View):
    def get(self, request):
        p_form = ParentUpdateForm(instance=request.user)
        u_form = UserUpdateForm(instance=request.user)

        context = {
            'p_form': p_form,
            'u_form': u_form,

        }
        return render(request, 'parent_profile_update.html', context)

    def post(self, request):
        p_form = ParentUpdateForm(request.POST, instance=request.user)
        u_form = UserUpdateForm(request.POST, instance=request.user)

        if p_form.is_valid() and u_form.is_valid():
            p_form.save()
            u_form.save()
            return redirect('parent_profile')
