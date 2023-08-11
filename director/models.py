from django.db import models
from accounts.models import User
from django.core.validators import RegexValidator
from PIL import Image
from django.utils.html import format_html


class Director(models.Model):
    first_name = models.CharField(max_length=128, null=True)
    last_name = models.CharField(max_length=128, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

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
    email_address = models.EmailField(null=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                 message="Numer telefonu w formacie: '+99 999 999 999'. Up to 15 digits allowed.")
    phone = models.CharField(null=True, unique=True, max_length=17, validators=[phone_regex])
    city = models.CharField(max_length=64, null=True)
    address = models.CharField(max_length=128, null=True)
    zip_code = models.CharField(null=True, max_length=6, validators=[RegexValidator(
        regex=r'^(^[0-9]{2}(?:-[0-9]{3})?$)?$)',
        message=(u'Format kodu pocztowego to - 12-123'),
    )], )
