from django import forms
from .models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
# from .models import Groups


class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email', 'password1', 'password2']

