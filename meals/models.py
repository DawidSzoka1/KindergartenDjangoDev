from django.db import models
from director.models import Director, MealPhotos
from groups.models import Groups


# Create your models here.

class Meals(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField(null=True)
    principal = models.ForeignKey(Director, on_delete=models.CASCADE, null=True)
    photo = models.ManyToManyField(MealPhotos)
    per_day = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        """
        String representation
        """
        return f'{self.name}'
