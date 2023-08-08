from django.db import models
from accounts.models import User
from django.core.validators import RegexValidator


class Director(models.Model):
    first_name = models.CharField(max_length=128, null=True)
    last_name = models.CharField(max_length=128, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    class Meta:
        permissions = [
            ("is_director", "Is the director of kindergarten")
            ]


class ContactModel(models.Model):
    director = models.OneToOneField(Director, on_delete=models.CASCADE)
    email_address = models.EmailField()
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                 message="Phone number must be entered in the format: '+99 999 999 999'. Up to 15 digits allowed.")
    phone = models.CharField(null=True, unique=True, max_length=17, validators=[phone_regex])
    city = models.CharField(max_length=64, null=True)
    address = models.CharField(max_length=128, null=True)
    zip_code = models.CharField(null=True, max_length=6, validators=[RegexValidator(
        regex=r'^(^[0-9]{2}(?:-[0-9]{3})?$)?$)',
        message=(u'Must be valid zipcode in formats or 12-123'),
    )], )
