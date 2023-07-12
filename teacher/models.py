from django.db import models
from accounts.models import User
# Create your models here.


class Teacher(models.Model):
    first_name = models.CharField(max_length=128, null=True)
    last_name = models.CharField(max_length=128, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    class Meta:
        permissions = [
            ("is_teacher", "Is the teacher of some group")
            ]
