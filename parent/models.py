from django.db import models
from accounts.models import User


# Create your models here.
class ParentA(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=128, null=True)
    last_name = models.CharField(max_length=128, null=True)

    def __str__(self):
        return f'{self.user.email} Profile'

    class Meta:
        permissions = [
            ("is_parent", 'parent permission')
        ]
