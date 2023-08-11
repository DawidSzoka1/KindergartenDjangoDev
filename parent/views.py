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


class ParentListView(PermissionRequiredMixin, ListView):
    permission_required = "director.is_director"
    model = ParentA
    template_name = 'parents-list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["parents"] = Director.objects.get(user=self.request.user.id).parenta_set.filter(is_active=True)
        return context


class DetailsParentView(PermissionRequiredMixin, UserPassesTestMixin, DetailView):
    permission_required = "director.is_director"
    model = ParentA
    template_name = 'parent-details.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context["parent"] = get_object_or_404(Director, user=self.request.user.id).parenta_set.get(
                id=context['parent'].id)
        except Exception:
            context["parent"] = None
        return context

    def test_func(self):
        parenta = self.get_object()
        if self.request.user == parenta.principal.first().user:
            return True
        return False


class ParentProfileView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.get_user_permissions() == {'parent.is_parent'}:
            p_form = ParentUpdateForm(instance=request.user.parenta)
            u_form = UserUpdateForm(instance=request.user)
            parent_logged = ParentA.objects.get(user=request.user.id)
            parent_kids = parent_logged.kid_set.filter(is_active=True)

            context = {
                'p_form': p_form,
                'u_form': u_form,
                'parent_logged': parent_logged,
                'parent_kids': parent_kids,

            }
            return render(request, 'parent_profile.html', context)
        raise PermissionDenied

    def post(self, request):
        p_form = ParentUpdateForm(request.POST, instance=request.user.parenta)
        u_form = UserUpdateForm(request.POST, instance=request.user)

        if p_form.is_valid() and u_form.is_valid():
            p_form.save()
            u_form.save()
            return redirect('parent_profile')


class ParentSearchView(LoginRequiredMixin, View):
    def get(self, request):
        return redirect('list_parent')

    def post(self, request):
        search = request.POST.get('search')
        if search:
            parents = ParentA.objects.filter(principal=Director.objects.get(user=request.user.id)).filter(
                user__email__icontains=search
            )
            return render(request, 'parents-list.html', {'parents': parents})
        return redirect('list_teachers')
