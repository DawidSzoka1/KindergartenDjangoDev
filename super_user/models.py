from django.db import models
from accounts.models import User
from django.utils.timezone import now


# Create your models here.
class PaymentPlan(models.Model):
    name = models.TextField()
    price = models.DecimalField(max_digits=7, decimal_places=2, default=500)


class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=128, null=True)
    last_name = models.CharField(max_length=128, null=True)

    def __str__(self):
        return f'{self.user.email} Profile'


class Groups(models.Model):
    name = models.CharField(max_length=128)


class Kid(models.Model):
    gender_choices = ((1, 'Chłopiec'), (2, 'Dziewczynka'))
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128, default='cos')
    parents = models.ManyToManyField(Parent)
    group = models.ForeignKey(Groups, on_delete=models.CASCADE)
    gender = models.IntegerField(choices=gender_choices, default=1)
    start = models.DateField(default=now())
    end = models.DateField(null=True)
    payment_plan = models.ForeignKey(PaymentPlan, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=2, null=True)


class Meals(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField(null=True)
