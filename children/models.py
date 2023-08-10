from django.db import models
from django.utils import timezone
from director.models import Director, GroupPhotos, MealPhotos
from django.core.validators import MinValueValidator


# Create your models here.
class Groups(models.Model):
    name = models.CharField(max_length=128)
    principal = models.ForeignKey(Director, on_delete=models.CASCADE, null=True)
    capacity = models.IntegerField(null=True, validators=[MinValueValidator(limit_value=1)])
    photo = models.ManyToManyField(GroupPhotos)

    def __str__(self):
        """
        String representation
        """
        return f'{self.name}'


class Meals(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField(null=True)
    principal = models.ForeignKey(Director, on_delete=models.CASCADE, null=True)
    photo = models.ManyToManyField(MealPhotos)

    def __str__(self):
        """
        String representation
        """
        return f'{self.name}'


class PaymentPlan(models.Model):
    name = models.TextField()
    price = models.DecimalField(max_digits=7, decimal_places=2, default=500)
    principal = models.ForeignKey(Director, on_delete=models.CASCADE, null=True)

    def __str__(self):
        """
        String representation
        """
        return f'{self.name}'


class Kid(models.Model):
    gender_choices = ((1, 'Chłopiec'), (2, 'Dziewczynka'))
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    group = models.ForeignKey(Groups, on_delete=models.CASCADE)
    gender = models.IntegerField(choices=gender_choices, default=1)
    start = models.DateField(default=timezone.now)
    end = models.DateField(null=True)
    payment_plan = models.ForeignKey(PaymentPlan, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    kid_meals = models.ManyToManyField(Meals)
    principal = models.ForeignKey(Director, on_delete=models.CASCADE, null=True)


presenceChoices = (
    (1, 'Nieobeconsc'),
    (2, 'Obecnosc'),
    (3, 'Planowana nieobecnosc'),
    (4, 'dzien wolny')
)


class PresenceModel(models.Model):
    day = models.DateField(default=timezone.now())
    kid = models.ForeignKey(Kid, on_delete=models.CASCADE)
    presenceType = models.IntegerField(choices=presenceChoices)
