from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from .models import Kid, Groups, PaymentPlan, Director
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.decorators import permission_required


class AddKid(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        groups = Groups.objects.all()
        plans = PaymentPlan.objects.all()
        return render(request, 'addKid.html', {"plans": plans, 'groups': groups})

    def post(self, request):

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
            user = Director.objects.get(user=request.user.id)
            user.kids.add(kid)

            return redirect('kids')

        return render(request, 'addKid.html', {"plans": self.plans, 'groups': self.groups})


class DirectorProfile(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        return render(request, 'director_profile.html')


class Kids(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        user = Director.objects.get(user=request.user.id)
        kids_db = user.kids.all()
        return render(request, 'kids_list.html', {"kids": kids_db})


class AddGroup(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        return render(request, 'addGroup.html')

    def post(self, request):
        name = request.POST.get('name')
        if name:
            user = Director.objects.get(user=request.user.id)
            group = Groups.objects.create(name=name)
            user.groups.add(group)
            return redirect('groups')
        return render(request, 'addGroup.html')


class GroupsView(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        user = Director.objects.get(user=request.user.id)
        groups = user.groups.all()
        return render(request, 'groups.html', {'groups': groups})


class PaymentPlans(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        user = Director.objects.get(user=request.user.id)
        plans = user.payment_plan.all()
        return render(request, 'payments.html', {"plans": plans})


class AddPaymentsPlan(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        return render(request, 'addPayment.html')

    def post(self, request):
        name = request.POST.get("name")
        price = float(request.POST.get("price"))
        if name and price:
            user = Director.objects.get(user=request.user.id)
            payment = PaymentPlan.objects.create(name=name, price=price)
            user.payment_plan.add(payment)
            return redirect('payments_plans')
        return render(request, 'addPayment.html')


class ChangeInfo(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        user = Director.objects.get(user=request.user.id)
        plans = user.payment_plan.all()
        groups = user.groups.all()
        kid_id = request.GET.get('kid_id')
        kid = user.kids.get(id=int(kid_id))
        return render(request, 'changePayment.html', {"plans": plans, "groups": groups, 'kid': kid})

    def post(self, request):
        plan = int(request.POST.get("plan"))
        group = int(request.POST.get('group'))
        plan = self.user.payment_plan.get(id=plan)
        group = self.user.groups.get(id=group)
        if plan and group:
            self.kid.group = group
            self.kid.payment_plan = plan
            self.kid.save()
            return redirect('childrens')
        return render(request, 'changePayment.html', {"plans": self.plans, "groups": self.groups, 'kid': self.kid})
