from django.db import models
from accounts.models import User
from director.models import Director, KindergartenOwnedModel
from children.models import Groups
from django.core.validators import RegexValidator

# Create your models here.

roles = (
    (1, 'pomoc'),
    (2, 'nauczyciel'),
    (3, 'inna')
)


class Employee(KindergartenOwnedModel):
    gender_choices = ((1, 'Mezczyzna'), (2, 'Kobieta'))
    first_name = models.CharField(max_length=128, null=True)
    last_name = models.CharField(max_length=128, null=True)
    role = models.IntegerField(choices=roles, default=3)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    group = models.ForeignKey(Groups, on_delete=models.CASCADE, null=True)
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
    gender = models.IntegerField(choices=gender_choices, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,  related_name='employee_profiles')
    is_active = models.BooleanField(default=True)

    class Meta:
        permissions = [
            ("is_teacher", "Is the teacher of some group")
        ]
        unique_together = ('user', 'kindergarten')

    def __str__(self):
        # Pobieramy imię i nazwisko z powiązanego modelu User
        return f"{self.first_name} {self.last_name} ({self.kindergarten.name})"
