from django.db import models
from director.models import Director, MealPhotos, KindergartenOwnedModel
from groups.models import Groups


# Create your models here.

class Meals(KindergartenOwnedModel):
    name = models.CharField(max_length=128)
    description = models.TextField(null=True)
    photo = models.ForeignKey(MealPhotos, on_delete=models.CASCADE, null=True)
    per_day = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        """
        String representation
        """
        return f'{self.name}'
