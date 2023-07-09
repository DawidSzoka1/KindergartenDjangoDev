from django.shortcuts import render, redirect
from django.views import View
from .forms import UserRegisterForm


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