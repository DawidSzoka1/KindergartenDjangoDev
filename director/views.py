from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from .models import Kid, Groups, PaymentPlan, Director, Meals
from django.contrib.auth.mixins import PermissionRequiredMixin
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


class AddKidView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        user = Director.objects.get(user=request.user.id)
        groups = user.groups.all()
        plans = user.payment_plan.all()
        meals = user.meals.all()
        if not plans:
            messages.error(request, 'Najpierw musisz dodac plan platniczy')
            return redirect('add_payment_plans')
        if not groups:
            messages.error(request, 'Najpierw musisz dodac jakas grupe')
            return redirect('add_group')
        if not meals:
            messages.error(request, 'Najpierw musisz dodac jakies posilki')
            return redirect('add_meal')
        return render(request, 'director-add-kid.html', {"plans": plans, 'groups': groups, 'meals': meals})

    def post(self, request):
        user = Director.objects.get(user=request.user.id)
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
        payment = PaymentPlan.objects.get(id=int(payment))
        group = Groups.objects.get(id=int(group))
        amount = payment.price
        if first_name and last_name and gender and payment and group and start:

            if end:
                kid = Kid.objects.create(first_name=first_name,
                                         last_name=last_name,
                                         group=group,
                                         gender=gender,
                                         start=start,
                                         payment_plan=payment,
                                         end=end,
                                         amount=amount
                                         )
            else:
                kid = Kid.objects.create(first_name=first_name,
                                         last_name=last_name,
                                         group=group,
                                         gender=gender,
                                         start=start,
                                         payment_plan=payment,
                                         amount=amount
                                         )
            for meal in meals:
                meal_object = Meals.objects.get(id=int(meal))
                kid.kid_meals.add(meal_object)
            user.kids.add(kid)

            return redirect('list_kids')
        messages.error(request, 'Wypelnij wszystkie pola')
        return redirect('add_kid')


class DirectorProfileView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        return render(request, 'director-profile.html')


class KidsListView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        user = Director.objects.get(user=request.user.id)
        kids_db = user.kids.all()
        return render(request, 'director-list-kids.html', {"kids": kids_db})


class AddMealView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        return render(request, 'director-add-meal.html')

    def post(self, request):
        name = request.POST.get('name')
        desc = request.POST.get('desc')
        if name and desc:
            meal = Meals.objects.create(name=name, description=desc)
            user = Director.objects.get(user=request.user.id)
            user.meals.add(meal)
            return redirect('list_meals')
        messages.error(request, 'Wypelnij wszystkie pola')
        return redirect('add_meal')


class MealsListView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        user = Director.objects.get(user=request.user.id)
        meals = user.meals.all()
        return render(request, 'director-list-meals.html', {'meals': meals})


class AddGroupView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        return render(request, 'director-add-group.html')

    def post(self, request):
        name = request.POST.get('name')
        if name:
            user = Director.objects.get(user=request.user.id)
            group = Groups.objects.create(name=name)
            user.groups.add(group)
            return redirect('list_groups')
        messages.error(request, 'Wypelnij wszystkie pola')
        return redirect('add_group')


class GroupsListView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        user = Director.objects.get(user=request.user.id)
        groups = user.groups.all()
        return render(request, 'director-list-groups.html', {'groups': groups})


class PaymentPlansListView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        user = Director.objects.get(user=request.user.id)
        plans = user.payment_plan.all()
        return render(request, 'director-list-payments-plans.html', {"plans": plans})


class AddPaymentsPlanView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        return render(request, 'director-add-payment-plans.html')

    def post(self, request):
        name = request.POST.get("name")
        price = request.POST.get("price")
        if name and price:
            user = Director.objects.get(user=request.user.id)
            payment = PaymentPlan.objects.create(name=name, price=float(price))
            user.payment_plan.add(payment)
            return redirect('list_payments_plans')
        messages.error(request, 'Wypelnij wszystkie pola')
        return redirect('add_payment_plans')


class ChangeKidInfoView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request, pk):
        user = Director.objects.get(user=request.user.id)
        plans = user.payment_plan.all()
        groups = user.groups.all()
        meals = user.meals.all()
        kid = user.kids.get(id=int(pk))
        return render(request, 'director-change-kid-info.html', {"plans": plans, "groups": groups, 'kid': kid, 'meals': meals})

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
        return render(request, 'director-change-kid-info.html', {"plans": plans, "groups": groups, 'kid': kid, 'meals': meals})


class InviteParentView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request, pk):
        user = Director.objects.get(user=request.user.id)
        kid = user.kids.get(id=int(pk))
        return render(request, 'director-invite-parent.html', {'kid': kid})

    def post(self, request):
        user = Director.objects.get(user=request.user.id)

        kid_id = request.GET.get('kid_id')
        kid = user.kids.get(id=int(kid_id))
        parent_email = request.POST.get('email')

        if parent_email:
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

            subject = f"Zaproszenie na konto przedszkola dla rodzica {kid.first_name}"
            from_email = EMAIL_HOST_USER
            text_content = "Marchewka zaprasza do korzystania z konto do ubslugi dzieci"
            html_content = render_to_string('email_to_parent.html', {'password': password})
            msg = EmailMultiAlternatives(subject, text_content, from_email, [parent_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            return redirect('list_kids')

        else:
            return render(request, 'director-invite-parent.html', {'kid': kid})


class DetailsKidView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request, pk):
        user = Director.objects.get(user=request.user.id)
        kid = user.kids.get(id=int(pk))
        return render(request, 'director-kid-details.html', {'kid': kid})
