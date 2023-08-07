from django.db import models
from accounts.models import User
from director.models import Director
from django.core.validators import RegexValidator
from children.models import Kid


# Create your models here.
class ParentA(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=128, null=True)
    last_name = models.CharField(max_length=128, null=True)
    kids = models.ManyToManyField(Kid)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                 message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone = models.CharField(null=True, unique=True, max_length=17, validators=[phone_regex])
    principal = models.ManyToManyField(Director)

    def __str__(self):
        return f'{self.user.email} Profile'

    class Meta:
        permissions = [
            ("is_parent", 'parent permission')
        ]
