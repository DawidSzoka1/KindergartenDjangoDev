from .models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms


class UserRegisterForm(UserCreationForm):
    kindergarten_name = forms.CharField(max_length=255, label="Nazwa Twojej Placówki", required=True)
    class Meta:
        model = User
        fields = ['email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        # Zwracamy email bez rzucania błędu ValidationError.
        # Django nie będzie już blokować formularza na tym etapie.
        return email

    def validate_unique(self):
        # Nadpisujemy tę metodę, aby uniemożliwić automatyczne sprawdzanie
        # unikalności maila przez model User podczas is_valid().
        pass
