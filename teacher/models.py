from django.db import models
from accounts.models import User
from director.models import Director
from children.models import Groups
from django.core.validators import RegexValidator
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
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                 message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone = models.CharField(null=True, unique=True, max_length=17, validators=[phone_regex])
    city = models.CharField(max_length=64, null=True)
    address = models.CharField(max_length=128, null=True)
    zip_code = models.CharField(null=True, max_length=6, validators=[RegexValidator(
        regex=r'^(^[0-9]{2}(?:-[0-9]{3})?$)?$)',
        message=(u'Must be valid zipcode in formats or 12-123'),
    )],)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    principal = models.ManyToManyField(Director)

    class Meta:
        permissions = [
            ("is_teacher", "Is the teacher of some group")
            ]
