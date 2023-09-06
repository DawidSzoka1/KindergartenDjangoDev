from django.shortcuts import render, redirect
from django.views import View
from .forms import UserRegisterForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages


class Register(View):
    def get(self, request):
        if request.user.is_active:
            messages.info(request, 'Masz juz konto')
            return redirect('home_page')
        form = UserRegisterForm()
        return render(request, "register.html", {'form': form})

    def post(self, request):
        if request.user.is_active:
            messages.info(request, 'Masz juz konto')
            return redirect('home_page')
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
        else:
            form = UserRegisterForm()
        return render(request, "register.html", {'form': form})


class ProfilePasswordUpdate(LoginRequiredMixin, View):
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

            return redirect('home_page')
        messages.error(request, 'wypelnij poprawnie formularz')
        return redirect('password_change')
