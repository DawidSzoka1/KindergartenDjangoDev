from django.db import models
from accounts.models import User
from django.core.validators import RegexValidator
from PIL import Image
from django.utils.html import format_html


class Kindergarten(models.Model):
    name = models.CharField(max_length=255, null=True , blank=True )


class KindergartenManager(models.Manager):
    def for_kindergarten(self, kindergarten_id):
        return self.get_queryset().filter(kindergarten_id=kindergarten_id)


# W modelu bazowym dodajesz:
class KindergartenOwnedModel(models.Model):
    kindergarten = models.ForeignKey(Kindergarten, on_delete=models.CASCADE, null=True)
    objects = KindergartenManager()  # Teraz masz metodę .for_kindergarten()

    class Meta:
        abstract = True


class Director(KindergartenOwnedModel):
    gender_choices = ((1, 'Mezczyzna'), (2, 'Kobieta'))
    first_name = models.CharField(max_length=128, null=True)
    last_name = models.CharField(max_length=128, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='director_profiles')
    gender = models.IntegerField(choices=gender_choices, null=True)

    class Meta:
        permissions = [
            ("is_director", "Is the director of kindergarten")
        ]
        unique_together = ('user', 'kindergarten')

    def __str__(self):
        return f"{self.user.email} - {self.kindergarten.name}"


def user_group_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/kindergarten_<id>/group/<filename>
    return "kindergarten_{0}/group/{1}".format(instance.kindergarten.id, filename)


def user_meal_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/kindergarten_<id>/meal/<filename>
    return "kindergarten_{0}/meal/{1}".format(instance.kindergarten.id, filename)


class GroupPhotos(KindergartenOwnedModel):
    group_photos = models.ImageField(null=True, upload_to=user_group_path, unique=True)
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


class MealPhotos(KindergartenOwnedModel):
    meal_photos = models.ImageField(null=True, upload_to=user_meal_path)
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


class FreeDaysModel(KindergartenOwnedModel):
    title = models.CharField(max_length=128)
    description = models.TextField(null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)


class ContactModel(KindergartenOwnedModel):

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
        # Teraz __str__ będzie znacznie bardziej czytelny w panelu admina
        return f"{self.kindergarten__name} ({self.city})"

    class Meta:
        verbose_name = "Dane kontaktowe"
        verbose_name_plural = "Dane kontaktowe"
