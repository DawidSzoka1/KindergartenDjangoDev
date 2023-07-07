from accounts.forms import ParentRegisterForm, TeacherRegisterForm
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from .models import Kid, Groups


@user_passes_test(lambda u: u.is_superuser)
def add_kid(request):
    groups = Groups.objects.all()
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        gender = 1 if request.POST.get("gender") == 'Chłopiec' else 2
        group = request.POST.get("group")
        meals = request.POST.getlist("meals")
        start = request.POST.get("start")
        indefinite = request.POST.get("indefinite")
        end = 0
        if not indefinite:
            end = request.POST.get("end")
        payment = request.POST.get("payment")
        group = Groups.objects.get(name=group)
        if first_name and last_name and gender:
            if end:
                Kid.objects.create(first_name=first_name,
                                   last_name=last_name,
                                   group=group,
                                   gender=gender,
                                   start=start,
                                   end=end,

                                   )
            else:
                Kid.objects.create(first_name=first_name,
                                   last_name=last_name,
                                   group=group,
                                   gender=gender,
                                   start=start,
                                   )

            return redirect('childrens')

        return render(request, 'addKid.html')
    return render(request, 'addKid.html', {"form": ParentRegisterForm(), 'groups': groups})


class RegisterTeacher(View):
    def get(self, request):
        return render(request, 'addKid.html', {"form": TeacherRegisterForm()})

    def post(self, request):
        form = TeacherRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('first_name')
            messages.success(request, f"Account created for {username}!")
            return redirect("home_page")
        return render(request, 'addKid.html', {"form": TeacherRegisterForm()})


class Settings(View):
    def get(self, request):
        return render(request, 'settings.html')


class Children(View):
    def get(self, request):
        kids = Kid.objects.all()
        return render(request, 'childrens.html', {"kids": kids})


@user_passes_test(lambda u: u.is_superuser)
def add_group(request):
    if request.method == "POST":
        name = request.POST.get('name')
        if name:
            Groups.objects.create(name=name)
            return redirect('groups')
    return render(request, 'addGroup.html')


class GroupsView(View):
    def get(self, request):
        groups = Groups.objects.all()
        return render(request, 'groups.html', {'groups': groups})


@user_passes_test(lambda u: u.is_superuser)
def payment_plans(request):
    if request.method == "POST":
        name = request.POST.get('name')
        if name:
            Groups.objects.create(name=name)
            return redirect('groups')
    return render(request, 'addGroup.html')
