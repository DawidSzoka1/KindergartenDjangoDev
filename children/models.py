from django.db import models
from django.utils import timezone
from director.models import Director, GroupPhotos, MealPhotos
from groups.models import Groups
from meals.models import Meals
from payments_plans.models import PaymentPlan


# Create your models here.


class Kid(models.Model):
    gender_choices = ((1, 'Chłopiec'), (2, 'Dziewczynka'))
    date_of_birth = models.DateField(null=True)
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    group = models.ForeignKey(Groups, on_delete=models.CASCADE, null=True)
    gender = models.IntegerField(choices=gender_choices, default=1)
    start = models.DateField(default=timezone.now)
    end = models.DateField(null=True)
    payment_plan = models.ForeignKey(PaymentPlan, on_delete=models.CASCADE, null=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    kid_meals = models.ForeignKey(Meals, on_delete=models.CASCADE, null=True)
    principal = models.ForeignKey(Director, on_delete=models.CASCADE, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        """
        String representation
        """
        return f'{self.first_name.title()} {self.last_name.title()}'


presenceChoices = (
    (1, 'Nieobeconsc'),
    (2, 'Obecnosc'),
    (3, 'Planowana nieobecnosc'),
    (4, 'dzien wolny')
)


class PresenceModel(models.Model):
    day = models.DateField(auto_created=True)
    kid = models.ForeignKey(Kid, on_delete=models.CASCADE)
    presenceType = models.IntegerField(choices=presenceChoices)
