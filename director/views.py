from django.shortcuts import render, redirect
from django.views import View
from .models import Kid, Groups, PaymentPlan, Director
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.mail import EmailMultiAlternatives
from MarchewkaDjango.settings import EMAIL_HOST_USER
from django.template.loader import render_to_string
from accounts.models import User
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from parentsAccounts.models import ParentA
from django.db.utils import IntegrityError


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


class InviteParent(PermissionRequiredMixin, View):
    permission_required = "director.is_director"

    def get(self, request):
        user = Director.objects.get(user=request.user.id)
        kid_id = request.GET.get('kid_id')
        kid = user.kids.get(id=int(kid_id))
        return render(request, 'invite_parent.html', {'kid': kid})

    def post(self, request):
        user = Director.objects.get(user=request.user.id)

        kid_id = request.GET.get('kid_id')
        kid = user.kids.get(id=int(kid_id))
        parent_email = request.POST.get('email')

        if parent_email:
            try:
                password = User.objects.make_random_password()
                parent_user = User.objects.create_user(email=parent_email, password=password)
                content_type = ContentType.objects.get_for_model(ParentA)
                permission = Permission.objects.get(content_type=content_type, codename='parentsAccounts')
                par_user = ParentA.objects.create(user=parent_user)
                user.parent_profiles.add(par_user)
                kid.parents.add(par_user)
                par_user.user.user_permissions.clear()
                par_user.user.user_permissions.add(permission)
                parent_user.parent.save()
            except:
                return render(request, "login.html")

            subject = f"Zaproszenie na konto przedszkola dla rodzica {kid.first_name}"
            from_email = EMAIL_HOST_USER
            text_content = "Marchewka zaprasza do korzustania z konto do ubslugi dzieci"
            html_content = render_to_string('email_to_parent.html', {'password': password})
            msg = EmailMultiAlternatives(subject, text_content, from_email, [parent_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            return redirect('kids')
        else:
            return render(request, 'invite_parent.html', {'kid': kid})
