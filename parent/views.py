from django.core.paginator import Paginator

from teacher.models import Employee
from .forms import ParentUpdateForm, UserUpdateForm
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from director.models import Director
from django.core.mail import EmailMultiAlternatives
from MarchewkaDjango.settings import EMAIL_HOST_USER
from django.template.loader import render_to_string
from accounts.models import User
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import ParentA
from django.core.exceptions import PermissionDenied
from children.models import Kid
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)


class InviteParentView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request, pk):
        user = Director.objects.get(user=request.user.id)
        kid = user.kid_set.get(id=int(pk))
        return render(request, 'parent-invite.html', {'kid': kid})

    def post(self, request, pk):
        user = Director.objects.get(user=request.user.id)
        kid = user.kid_set.get(id=int(pk))
        parent_email = request.POST.get('email')

        if parent_email:
            try:
                test = User.objects.get(email=parent_email)
            except User.DoesNotExist:
                test = None
            if test:
                messages.error(request, 'Ten rodzic juz istnieje')
                return redirect('invite_parent', pk=pk)
            try:
                password = User.objects.make_random_password()
                parent_user = User.objects.create_user(email=parent_email, password=password)
                content_type = ContentType.objects.get_for_model(ParentA)
                permission = Permission.objects.get(content_type=content_type, codename='is_parent')
                par_user = ParentA.objects.create(user=parent_user)
                par_user.principal.add(user)
                par_user.kids.add(kid)
                par_user.user.user_permissions.clear()
                par_user.user.user_permissions.add(permission)
                parent_user.parenta.save()
            except Exception as e:
                User.objects.filter(email=parent_email).first().delete()
                messages.error(request, f'Wystąpił blad {e}')
                return redirect('invite_parent', pk=pk)

            subject = f"Zaproszenie na konto przedszkola dla rodzica {kid.first_name}"
            from_email = EMAIL_HOST_USER
            text_content = "Marchewka zaprasza do korzystania z konto do ubslugi dzieci"
            html_content = render_to_string('email_to_parent.html', {'password': password, 'email': parent_email})
            msg = EmailMultiAlternatives(subject, text_content, from_email, [parent_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            messages.success(request, f"Udalo sie zaprosic rodzica o emailu {parent_email} ")
            return redirect('list_kids')

        else:
            messages.error(request, 'wypelnij formularz')
            return redirect('invite_parent', pk=pk)


class ParentListView(LoginRequiredMixin, View):

    def get(self, request):
        user = request.user
        if user.get_user_permissions() == {'director.is_director'}:
            director = get_object_or_404(Director, user=user.id)
            parents = director.parenta_set.all().order_by('-id')
        elif user.get_user_permissions() == {'teacher.is_teacher'}:
            teacher = get_object_or_404(Employee, user=user.id)
            kids = teacher.group.kid_set.filter(is_active=True).values_list('parenta', flat=True)
            all_parents = teacher.principal.first().parenta_set.all().order_by('-id')
            parents = []
            for parent in all_parents:
                if parent.id in kids:
                    parents.append(parent)
        else:
            raise PermissionDenied
        paginator = Paginator(parents, 15)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        return render(request, 'parents-list.html', {'page_obj': page_obj})

    def post(self, request):
        user = request.user
        director = get_object_or_404(Director, user=user.id)
        search = request.POST.get('search')
        if search:
            parents = director.parenta_set.filter(user__email__icontains=search).order_by('-id')
            paginator = Paginator(parents, 5)
            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)
            return render(request, 'parents-list.html', {'page_obj': page_obj})
        return redirect('list_parent')


class ParentProfileView(LoginRequiredMixin, View):
    def get(self, request, pk):
        user = request.user
        parent = get_object_or_404(ParentA, id=int(pk))
        p_form = ParentUpdateForm(instance=parent)
        u_form = UserUpdateForm(instance=parent.user)
        parent_kids = parent.kids.filter(is_active=True)

        context = {
            'p_form': p_form,
            'u_form': u_form,
            'parent_logged': parent,
            'parent_kids': parent_kids,

        }
        if user.get_user_permissions() == {'parent.is_parent'}:
            if parent.user.email == user.email:
                return render(request, 'parent_profile.html', context)
        elif user.get_user_permissions() == {'director.is_director'}:
            director = get_object_or_404(Director, user=user.id)
            if parent in director.parenta_set.all():
                return render(request, 'parent_profile.html', context)
        elif user.get_user_permissions() == {'teacher.is_teacher'}:
            teacher = get_object_or_404(Employee, user=user.id)
            if parent.kids.filter(group=teacher.group).filter(is_active=True):
                return render(request, 'parent_profile.html', context)

        raise PermissionDenied


    # def post(self, request):
    #     p_form = ParentUpdateForm(request.POST, instance=request.user.parenta)
    #     u_form = UserUpdateForm(request.POST, instance=request.user)
    #
    #     if p_form.is_valid() and u_form.is_valid():
    #         p_form.save()
    #         u_form.save()
    #         return redirect('parent_profile')
    #     messages.error(request, f'{u_form.errors} i {p_form.errors}')
    #     return redirect('parent_profile')


class ParentDeleteView(PermissionRequiredMixin, View):
    permission_required = 'director.is_director'

    def post(self, request, pk):
        parent = get_object_or_404(ParentA, id=int(pk))
        if parent.principal.first().user.email == request.user.email:
            user = User.objects.get(parent=parent.id)
            user.delete()
            messages.success(request, f'Rodzic {user} został usniety')
            return redirect('list_parent')
        raise PermissionDenied


class ParentSearchView(LoginRequiredMixin, View):
    def get(self, request):
        return redirect('list_parent')

    def post(self, request):
        search = request.POST.get('search')
        if search:
            parents = ParentA.objects.filter(principal=Director.objects.get(user=request.user.id)).filter(
                user__email__icontains=search
            )
            paginator = Paginator(parents, 5)
            page_number = request.POST.get('page')
            page_obj = paginator.get_page(page_number)
            parents = page_obj
            return render(request, 'parents-list.html', {'parents': parents, 'page_obj': page_obj})
        return redirect('list_parent')
