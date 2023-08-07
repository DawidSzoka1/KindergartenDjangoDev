from django.db import models
from accounts.models import User
from director.models import Director
from children.models import Groups
# Create your models here.

roles = (
    (1, 'pomoc'),
    (2, 'nauczyciel'),
    (3, 'inna')
)


class Teacher(models.Model):
    first_name = models.CharField(max_length=128, null=True)
    last_name = models.CharField(max_length=128, null=True)
    role = models.IntegerField(choices=roles, default=3)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    group = models.ManyToManyField(Groups)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    principal = models.ManyToManyField(Director)

    class Meta:
        permissions = [
            ("is_teacher", "Is the teacher of some group")
            ]
