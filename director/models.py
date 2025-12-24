from django.db import models
from accounts.models import User
from django.core.validators import RegexValidator
from PIL import Image
from django.utils.html import format_html


class Director(models.Model):
    gender_choices = ((1, 'Mezczyzna'), (2, 'Kobieta'))
    first_name = models.CharField(max_length=128, null=True)
    last_name = models.CharField(max_length=128, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.IntegerField(choices=gender_choices, null=True)

    class Meta:
        permissions = [
            ("is_director", "Is the director of kindergarten")
        ]

    def __str__(self):
        return f"{self.user.email}"


def user_group_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/group/<filename>
    return "director_{0}/group/{1}".format(instance.principal.user.id, filename)


def user_meal_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/meal/<filename>
    return "director_{0}/meal/{1}".format(instance.principal.user.id, filename)


class GroupPhotos(models.Model):
    group_photos = models.ImageField(null=True, upload_to=user_group_path, unique=True)
    principal = models.ForeignKey(Director, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=64, null=True)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.group_photos:
            img = Image.open(self.group_photos.path)

            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.group_photos.path)

    def __str__(self):
        return f'{self.group_photos.url}'


class MealPhotos(models.Model):
    meal_photos = models.ImageField(null=True, upload_to=user_meal_path)
    principal = models.ForeignKey(Director, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=64, null=True)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.meal_photos:
            img = Image.open(self.meal_photos.path)

            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.meal_photos.path)

    def __str__(self):
        return f'{self.meal_photos.url}'


class FreeDaysModel(models.Model):
    principal = models.ForeignKey(Director, on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    description = models.TextField(null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)


class ContactModel(models.Model):
    director = models.OneToOneField(Director, on_delete=models.CASCADE)

    # Podstawowe dane kontaktowe
    email_address = models.EmailField(null=True, verbose_name="E-mail placówki")
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                 message="Numer telefonu w formacie: '+99 999 999 999'")
    phone = models.CharField(null=True, unique=True, max_length=17, validators=[phone_regex], verbose_name="Telefon")

    # Rozbite pole lokalizacji (lepsze dla szablonów niż jeden TextField)
    address = models.CharField(max_length=255, null=True, verbose_name="Ulica i numer")
    zip_code = models.CharField(max_length=10, null=True, verbose_name="Kod pocztowy")
    city = models.CharField(max_length=100, null=True, verbose_name="Miasto")

    # Dodatkowe przydatne informacje
    office_hours = models.CharField(max_length=100, default="08:00 - 16:00", verbose_name="Godziny otwarcia biura")
    website_url = models.URLField(null=True, blank=True, verbose_name="Strona WWW")

    # Pole tekstowe na dodatkowe informacje (np. dojazd)
    additional_info = models.TextField(max_length=500, null=True, blank=True, verbose_name="Dodatkowe informacje")

    def __str__(self):
        return f"Kontakt: {self.director.user.first_name} - {self.city}"

    class Meta:
        verbose_name = "Dane kontaktowe"
        verbose_name_plural = "Dane kontaktowe"
