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
    start = models.DateField(auto_created=True)
    end = models.DateField(null=True)
    payment_plan = models.ForeignKey(PaymentPlan, on_delete=models.CASCADE, null=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    kid_meals = models.ForeignKey(Meals, on_delete=models.CASCADE, null=True)
    principal = models.ForeignKey(Director, on_delete=models.CASCADE, null=True)
    is_active = models.BooleanField(default=True)

    def years_old(self):
        return timezone.now().year - self.date_of_birth.year

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



class Invoice(models.Model):
    STATUS_CHOICES = (
        ('unpaid', 'Nieopłacona'),
        ('partial', 'Opłacona częściowo'),
        ('paid', 'Opłacona'),
        ('overdue', 'Zaległość'),
    )

    kid = models.ForeignKey(Kid, on_delete=models.CASCADE, related_name='invoices')
    month = models.IntegerField(verbose_name="Miesiąc")
    year = models.IntegerField(verbose_name="Rok")
    principal = models.ForeignKey(Director, on_delete=models.CASCADE, related_name='invoices', null=True)

    # Kwoty składowe (zapisujemy je na stałe w momencie wygenerowania faktury)
    tuition_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Czesne")
    meals_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Wyżywienie")
    arrears_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Zaległości")

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Suma do zapłaty")
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Kwota wpłacona")

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unpaid')
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(verbose_name="Termin płatności")

    class Meta:
        unique_together = ('kid', 'month', 'year') # Jedno rozliczenie na dziecko w miesiącu
        verbose_name = "Rozliczenie"
        verbose_name_plural = "Rozliczenia"

    def __str__(self):
        return f"Faktura {self.month}/{self.year} - {self.kid}"

    @property
    def remaining_amount(self):
        return self.total_amount - self.paid_amount
