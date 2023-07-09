from django.shortcuts import render, redirect
from django.views import View
from .forms import UserRegisterForm


class Register(View):
    def get(self, request):
        form = UserRegisterForm()
        return render(request, "register.html", {'form': form})
