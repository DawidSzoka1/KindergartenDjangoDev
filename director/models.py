from django.db import models
from parentsAccounts.models import ParentA
from accounts.models import User
from django.utils import timezone


# Create your models here.
class PaymentPlan(models.Model):
    name = models.TextField()
    price = models.DecimalField(max_digits=7, decimal_places=2, default=500)


class Groups(models.Model):
    name = models.CharField(max_length=128)


class Kid(models.Model):
    gender_choices = ((1, 'Chłopiec'), (2, 'Dziewczynka'))
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128, default='cos')
    group = models.ForeignKey(Groups, on_delete=models.CASCADE)
    gender = models.IntegerField(choices=gender_choices, default=1)
    start = models.DateField(default=timezone.now())
    end = models.DateField(null=True)
    payment_plan = models.ForeignKey(PaymentPlan, on_delete=models.CASCADE)
    parents = models.ManyToManyField(ParentA)
    amount = models.DecimalField(max_digits=20, decimal_places=2, null=True)


class Meals(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField(null=True)


class Director(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    kids = models.ManyToManyField(Kid)
    meals = models.ManyToManyField(Meals)
    groups = models.ManyToManyField(Groups)
    payment_plan = models.ManyToManyField(PaymentPlan)
    parent_profiles = models.ManyToManyField(ParentA)

    class Meta:
        permissions = [
            ("is_director", "Is the director of kindergarten")
            ]
