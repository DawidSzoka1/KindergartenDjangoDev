from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from .models import Kid, Groups, PaymentPlan, SuperUser
from django.core.exceptions import PermissionDenied


# @user_passes_test(lambda u: u.is_superuser)
def add_kid(request):
    if request.user.user_permissions == "director":
        groups = Groups.objects.all()
        plans = PaymentPlan.objects.all()
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
                user = SuperUser.objects.get(user=request.user.id)
                user.kids.add(kid)

                return redirect('childrens')

            return render(request, 'addKid.html', {"plans": plans, 'groups': groups})
        return render(request, 'addKid.html', {"plans": plans, 'groups': groups})
    else:
        raise PermissionDenied()


def director_profile(request):
    return render(request, 'director_profile.html')


def kids(request):
    if request.user.user_permissions == "director":
        user = SuperUser.objects.get(user=request.user.id)
        kids_db = user.kids.all()
        return render(request, 'kids_list.html', {"kids": kids_db})
    else:
        raise PermissionDenied()


def add_group(request):
    if request.method == "POST":
        name = request.POST.get('name')
        if name:
            user = SuperUser.objects.get(user=request.user.id)
            group = Groups.objects.create(name=name)
            user.groups.add(group)
            return redirect('groups')
    return render(request, 'addGroup.html')


def groups_view(request):
    user = SuperUser.objects.get(user=request.user.id)
    groups = user.groups.all()
    return render(request, 'groups.html', {'groups': groups})


def payment_plans(request):
    user = SuperUser.objects.get(user=request.user.id)
    plans = user.payment_plan.all()
    return render(request, 'payments.html', {"plans": plans})


def add_payment_plans(request):
    if request.method == "POST":
        name = request.POST.get("name")
        price = float(request.POST.get("price"))
        if name and price:
            user = SuperUser.objects.get(user=request.user.id)
            payment = PaymentPlan.objects.create(name=name, price=price)
            user.payment_plan.add(payment)
            return redirect('payments_plans')
    return render(request, 'addPayment.html')


def change_info(request):
    user = SuperUser.objects.get(user=request.user.id)
    plans = user.payment_plan.all()
    group = user.groups.all()
    kid_id = request.GET.get('kid_id')
    kid = user.kids.get(id=int(kid_id))
    if request.method == "POST":
        plan = int(request.POST.get("plan"))
        group = int(request.POST.get('group'))
        plan = user.payment_plan.get(id=plan)
        group = user.groups.get(id=group)
        if plan and group:
            kid.group = group
            kid.payment_plan = plan
            kid.save()
            return redirect('childrens')
    return render(request, 'changePayment.html', {"plans": plans, "groups": group, 'kid': kid})
