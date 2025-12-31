from django.db import models
from accounts.models import User
from director.models import Director, KindergartenOwnedModel
from django.core.validators import RegexValidator
from children.models import Kid


# Create your models here.
class ParentA(KindergartenOwnedModel):
    gender_choices = ((1, 'Mezczyzna'), (2, 'Kobieta'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='parent_profiles')
    first_name = models.CharField(max_length=128, null=True)
    last_name = models.CharField(max_length=128, null=True)
    kids = models.ManyToManyField(Kid)
    gender = models.IntegerField(choices=gender_choices, null=True)
    phone_regex = RegexValidator(regex=r'^(?<!\w)(\(?(\+|00)?48\)?)?[ -]?\d{3}[ -]?\d{3}[ -]?\d{3}(?!\w)$',
                                 message="Numer telefony musi byc w formie: '+48 999 999 999' albo '(+48 999 999 999)' albo '999 999 999'.",
                                 code='invalid_numer_telefonu')
    phone = models.CharField(null=True, unique=True, max_length=17, validators=[phone_regex])
    city = models.CharField(max_length=64, null=True)
    address = models.CharField(max_length=128, null=True)
    zip_code = models.CharField(null=True, max_length=6, validators=[RegexValidator(
        regex=r'^([0-9]{2}-[0-9]{3})$',
        message=(u'Kod pocztowy musi byc w formacie 00-000'),
        code="invalid_zip_code",
    )])
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.user.email} Profile'

    class Meta:
        permissions = [
            ("is_parent", 'parent permission')
        ]
        unique_together = ('user', 'kindergarten')