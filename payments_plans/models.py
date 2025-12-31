from django.db import models
from director.models import Director, KindergartenOwnedModel
from groups.models import Groups


# Create your models here.


class PaymentPlan(KindergartenOwnedModel):
    FREQUENCY_CHOICES = (
        ('monthly', 'Miesięcznie'),
        ('quarterly', 'Kwartalnie'),
        ('annually', 'Rocznie'),
        ('onetime', 'Jednorazowo'),
    )

    name = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=7, decimal_places=2, default=500)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly')
    discount_info = models.CharField(max_length=255, null=True, blank=True) # np. Sibling Discount (10%)
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name} - {self.price} zł'




from teacher.models import Employee

class SalaryPayment(KindergartenOwnedModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salary_payments')
    month = models.IntegerField()
    year = models.IntegerField()
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Pensja zasadnicza")
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Premia")

    is_paid = models.BooleanField(default=False, verbose_name="Czy wypłacono?")
    payment_date = models.DateField(null=True, blank=True, verbose_name="Data przelewu")

    class Meta:
        unique_together = ('employee', 'month', 'year')
        verbose_name = "Wypłata"
        verbose_name_plural = "Wypłaty"

    def __str__(self):
        return f"Pensja {self.month}/{self.year} - {self.employee}"
