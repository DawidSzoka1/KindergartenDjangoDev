from django.db import models
from director.models import Director
from groups.models import Groups


# Create your models here.


class PaymentPlan(models.Model):
    name = models.CharField(max_length=128)
    price = models.DecimalField(max_digits=7, decimal_places=2, default=500)
    principal = models.ForeignKey(Director, on_delete=models.CASCADE, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        """
        String representation
        """
        return f'{self.name}'
