from django import forms
from accounts.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import ParentA


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']


class ParentUpdateForm(forms.ModelForm):
    class Meta:
        model = ParentA
        fields = ['first_name', 'last_name']
