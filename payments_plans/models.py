from django.db import models
from director.models import Director
from groups.models import Groups


# Create your models here.


class PaymentPlan(models.Model):
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
    principal = models.ForeignKey(Director, on_delete=models.CASCADE, null=True)
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name} - {self.price} zł'