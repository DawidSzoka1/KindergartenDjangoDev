from django.shortcuts import render, redirect
from django.views import View
from .forms import UserRegisterForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm


class Register(View):
    def get(self, request):
        form = UserRegisterForm()
        return render(request, "register.html", {'form': form})

    def post(self, request):
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            return redirect('login')
        else:
            form = UserRegisterForm()
        return render(request, "register.html", {'form': form})


class ParentProfileUpdate(View):
    def get(self, request):

        password_form = PasswordChangeForm(request.user)

        context = {
            'password_form': password_form,
        }
        return render(request, 'change_password.html', context)

    def post(self, request):
        password_form = PasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            if user.user_permissions == 'parent.is_parent':
                return redirect('parent_profile')
