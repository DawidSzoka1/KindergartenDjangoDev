from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import KidAddForm, PaymentPlanForm, MealsForm, GroupsForm
from .models import Kid, Groups, PaymentPlan, Director, Meals
from teacher.models import Teacher
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.core.mail import EmailMultiAlternatives
from MarchewkaDjango.settings import EMAIL_HOST_USER
from django.template.loader import render_to_string
from accounts.models import User
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from parent.models import ParentA
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)


class DirectorProfileView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        return render(request, 'director-profile.html')


class AddPaymentsPlanView(PermissionRequiredMixin, CreateView):
    permission_required = "director.is_director"
    model = PaymentPlan
    template_name = 'director-add-payment-plans.html'
    form_class = PaymentPlanForm
    success_url = reverse_lazy('list_payments_plans')

    def form_valid(self, form):
        form.instance.save()
        Director.objects.get(user=self.request.user.id).payment_plan.add(form.instance)
        return super().form_valid(form)


class PaymentPlansListView(PermissionRequiredMixin, ListView):
    permission_required = "director.is_director"
    model = PaymentPlan
    template_name = 'director-list-payments-plans.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["plans"] = Director.objects.get(user=self.request.user.id).payment_plan.all()
        return context


class AddMealView(PermissionRequiredMixin, CreateView):
    permission_required = "director.is_director"
    model = Meals
    template_name = 'director-add-meal.html'
    form_class = MealsForm
    success_url = reverse_lazy('list_meals')

    def form_valid(self, form):
        form.instance.save()
        Director.objects.get(user=self.request.user.id).meals.add(form.instance)
        return super().form_valid(form)


class MealsListView(PermissionRequiredMixin, ListView):
    permission_required = "director.is_director"
    model = Meals
    template_name = 'director-list-meals.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meals"] = Director.objects.get(user=self.request.user.id).meals.all()
        return context


class AddGroupView(PermissionRequiredMixin, CreateView):
    permission_required = "director.is_director"
    model = Groups
    template_name = 'director-add-group.html'
    form_class = GroupsForm
    success_url = reverse_lazy('list_groups')

    def get_form(self, form_class=None):
        form = super(AddGroupView, self).get_form(form_class)
        form.fields['teachers'].required = False
        return form

    def form_valid(self, form):
        form.instance.save()
        Director.objects.get(user=self.request.user.id).groups.add(form.instance)
        return super().form_valid(form)


class GroupsListView(PermissionRequiredMixin, ListView):
    permission_required = "director.is_director"
    model = Groups
    template_name = 'director-list-groups.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["groups"] = Director.objects.get(user=self.request.user.id).groups.all()
        return context


class AddKidView(PermissionRequiredMixin, UserPassesTestMixin, CreateView):
    permission_required = "director.is_director"
    model = Kid
    template_name = 'director-add-kid.html'
    form_class = KidAddForm
    success_url = reverse_lazy('list_kids')

    def get_form_kwargs(self, **kwargs):
        """ Passes the request object to the form class.
         This is necessary to only display members that belong to a given user"""

        kwargs = super(AddKidView, self).get_form_kwargs()
        kwargs.update({'current_user': self.request.user})
        return kwargs

    def get_form(self, form_class=None):
        form = super(AddKidView, self).get_form(form_class)
        form.fields['end'].required = False
        return form

    def form_valid(self, form):
        form.instance.save(commit=False)
        Director.objects.get(user=self.request.user.id).kids.add(form.instance)
        form.instance.save()
        return super().form_valid(form)

    def test_func(self):
        director = Director.objects.get(user=self.request.user.id)
        if director.groups.all():
            if director.meals.all():
                if director.payment_plan.all():
                    return True
        return False

    def handle_no_permission(self):
        director = Director.objects.get(user=self.request.user.id)
        if not director.groups.all():
            messages.error(self.request, 'Dodaj najpierw jakas grupe')
            return redirect('add_group')
        if not director.meals.all():
            messages.error(self.request, 'Dodaj najpierw jakis posilke')
            return redirect('add_meal')
        if not director.payment_plan.alL():
            messages.error(self.request, 'Dodaj najpierw jakis plan platniczy')
            return redirect('add_payment_plans')

        return redirect('add_meal')


class KidsListView(PermissionRequiredMixin, ListView):
    permission_required = "director.is_director"
    model = Kid
    template_name = 'director-list-kids.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["kids"] = Director.objects.get(user=self.request.user.id).kids.all()
        return context


class DetailsKidView(PermissionRequiredMixin, UserPassesTestMixin, DetailView):
    permission_required = "director.is_director"
    model = Kid
    template_name = 'director-kid-details.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context["kid"] = get_object_or_404(Director, user=self.request.user.id).kids.get(id=context['kid'].id)
        except Exception:
            context["kid"] = None
        return context

    def test_func(self):
        kid = self.get_object()
        if self.request.user == kid.director_set.first().user:
            return True
        return False


class ChangeKidInfoView(PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    permission_required = "director.is_director"

    def get(self, request, pk):
        user = Director.objects.get(user=request.user.id)
        plans = user.payment_plan.all()
        groups = user.groups.all()
        meals = user.meals.all()
        kid = user.kids.get(id=int(pk))
        return render(request, 'director-change-kid-info.html',
                      {"plans": plans, "groups": groups, 'kid': kid, 'meals': meals})

    def post(self, request):
        user = Director.objects.get(user=request.user.id)
        plans = user.payment_plan.all()
        groups = user.groups.all()
        meals = user.meals.all()
        kid_id = request.GET.get('kid_id')
        kid = user.kids.get(id=int(kid_id))
        plan = int(request.POST.get("plan"))
        group = int(request.POST.get('group'))
        meals_to_change = request.POST.getlist('meals')

        plan = user.payment_plan.get(id=plan)
        group = user.groups.get(id=group)
        if plan and group and meals_to_change:
            kid.kid_meals.clear()
            for meal in meals_to_change:
                objec = user.meals.get(id=int(meal))
                kid.kid_meals.add(objec)
            kid.group = group
            kid.payment_plan = plan
            kid.save()
            return redirect('list_kids')
        return render(request, 'director-change-kid-info.html',
                      {"plans": plans, "groups": groups, 'kid': kid, 'meals': meals})


class InviteParentView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request, pk):
        user = Director.objects.get(user=request.user.id)
        kid = user.kids.get(id=int(pk))
        return render(request, 'director-invite-parent.html', {'kid': kid})

    def post(self, request, pk):
        user = Director.objects.get(user=request.user.id)
        kid = user.kids.get(id=int(pk))
        parent_email = request.POST.get('email')

        if parent_email:
            try:
                test = User.objects.get(email=parent_email)
            except User.DoesNotExist:
                test = None
            if test:
                messages.error(request, 'Ten rodzic juz istnieje')
                return redirect('add_teacher')
            try:
                password = User.objects.make_random_password()
                parent_user = User.objects.create_user(email=parent_email, password=password)
                content_type = ContentType.objects.get_for_model(ParentA)
                permission = Permission.objects.get(content_type=content_type, codename='is_parent')
                par_user = ParentA.objects.create(user=parent_user)
                user.parent_profiles.add(par_user)
                kid.parents.add(par_user)
                par_user.user.user_permissions.clear()
                par_user.user.user_permissions.add(permission)
                parent_user.parenta.save()
            except Exception as e:
                User.objects.filter(email=parent_email).first().delete()
                messages.error(request, f'Wystąpił blad {e}')
                return redirect('add_teacher')

            subject = f"Zaproszenie na konto przedszkola dla rodzica {kid.first_name}"
            from_email = EMAIL_HOST_USER
            text_content = "Marchewka zaprasza do korzystania z konto do ubslugi dzieci"
            html_content = render_to_string('email_to_parent.html', {'password': password, 'email': parent_email})
            msg = EmailMultiAlternatives(subject, text_content, from_email, [parent_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            return redirect('list_kids')

        else:
            return render(request, 'director-invite-parent.html', {'kid': kid})


class TeachersListView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        user = Director.objects.get(user=request.user.id)
        teachers = user.teachers.all()
        return render(request, 'director-list-teachers.html', {'teachers': teachers})


class AddTeacherView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        user = Director.objects.get(user=request.user.id)
        groups = user.groups.all()
        return render(request, 'director-add-teacher.html', {'groups': groups})

    def post(self, request):
        user = Director.objects.get(user=request.user.id)
        group_id = request.POST.get('group')
        group = user.groups.get(id=int(group_id))
        teacher_email = request.POST.get('email')
        if teacher_email:
            try:
                test = User.objects.get(email=teacher_email)
            except User.DoesNotExist:
                test = None
            if test:
                messages.error(request, 'Ten nauczyciel juz istnieje')
                return redirect('add_teacher')
            try:
                password = User.objects.make_random_password()
                teacher_user = User.objects.create_user(email=teacher_email, password=password)
                content_type = ContentType.objects.get_for_model(Teacher)
                permission = Permission.objects.get(content_type=content_type, codename='is_teacher')
                teacher_object = Teacher.objects.create(user=teacher_user)
                user.teachers.add(teacher_object)
                group.teachers.add(teacher_object)
                teacher_object.user.user_permissions.clear()
                teacher_object.user.user_permissions.add(permission)
                teacher_user.teacher.save()
            except Exception as e:
                User.objects.filter(email=teacher_email).first().delete()

                messages.error(request, f'Wystąpił blad {e}')
                return redirect('add_teacher')
            subject = f"Zaproszenie na konto przedszkola dla nauczyciela"
            from_email = EMAIL_HOST_USER
            text_content = "Marchewka zaprasza do korzystania z konto jako nauczyciel"
            html_content = render_to_string('email_to_parent.html', {'password': password, 'email': teacher_email})
            msg = EmailMultiAlternatives(subject, text_content, from_email, [teacher_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            return redirect('list_teachers')

        else:
            messages.error(request, 'wypelnij wszystkie pola')
            return redirect('add_teacher')
