from django.db import models
from director.models import Director, GroupPhotos, MealPhotos
from django.core.validators import MinValueValidator


# Create your models here.
class Groups(models.Model):
    name = models.CharField(max_length=128)
    principal = models.ForeignKey(Director, on_delete=models.CASCADE, null=True)
    capacity = models.IntegerField(null=True, validators=[MinValueValidator(limit_value=1)])
    photo = models.ManyToManyField(GroupPhotos)
    is_active = models.BooleanField(default=True)
    yearbook = models.IntegerField(null=True)

    def __str__(self):
        """
        String representation
        """
        return f'{self.name}'
