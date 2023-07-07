from accounts.forms import ParentRegisterForm, TeacherRegisterForm
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from .models import Kid, Groups, PaymentPlan


@user_passes_test(lambda u: u.is_superuser)
def add_kid(request):
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
                Kid.objects.create(first_name=first_name,
                                   last_name=last_name,
                                   group=group,
                                   gender=gender,
                                   start=start,
                                   payment_plan=payment,
                                   end=end,
                                   amount=amount

                                   )
            else:
                Kid.objects.create(first_name=first_name,
                                   last_name=last_name,
                                   group=group,
                                   gender=gender,
                                   start=start,
                                   payment_plan=payment,
                                   amount=amount
                                   )

            return redirect('childrens')

        return render(request, 'addKid.html', {"plans": plans, 'groups': groups})
    return render(request, 'addKid.html', {"plans": plans, 'groups': groups})


@user_passes_test(lambda u: u.is_superuser)
def super_profile(request):

    return render(request, 'settings.html')


@user_passes_test(lambda u: u.is_superuser)
def kids(request):
    kids_db = Kid.objects.all()
    return render(request, 'childrens.html', {"kids": kids_db})


@user_passes_test(lambda u: u.is_superuser)
def add_group(request):
    if request.method == "POST":
        name = request.POST.get('name')
        if name:
            Groups.objects.create(name=name)
            return redirect('groups')
    return render(request, 'addGroup.html')


@user_passes_test(lambda u: u.is_superuser)
def groups_view(request):
    groups = Groups.objects.all()
    return render(request, 'groups.html', {'groups': groups})


@user_passes_test(lambda u: u.is_superuser)
def payment_plans(request):
    plans = PaymentPlan.objects.all()
    return render(request, 'payments.html', {"plans": plans})


@user_passes_test(lambda u: u.is_superuser)
def add_payment_plans(request):
    if request.method == "POST":
        name = request.POST.get("name")
        price = float(request.POST.get("price"))
        if name and price:
            PaymentPlan.objects.create(name=name, price=price)
            return redirect('payments_plans')
    return render(request, 'addPayment.html')


@user_passes_test(lambda u: u.is_superuser)
def change_info(request):
    if request.method == "GET":
        kid_id = request.GET.get('kid_id')
        kid = Kid.objects.get(id=int(kid_id))
    plans = PaymentPlan.objects.all()
    group = Groups.objects.all()
    if request.method == "POST":
        kid_id = request.GET.get('kid_id')
        kid = Kid.objects.get(id=int(kid_id))
        plan = int(request.POST.get("plan"))
        group = int(request.POST.get('group'))
        plan = PaymentPlan.objects.get(id=plan)
        group = Groups.objects.get(id=group)
        if plan and group:
            kid.group = group
            kid.payment_plan = plan
            kid.save()
            return redirect('childrens')
    return render(request, 'changePayment.html', {"plans": plans, "groups": group, 'kid': kid})
