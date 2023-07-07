from django import forms
from .models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
# from .models import Groups


class ParentRegisterForm(UserCreationForm):
    genders = (
        ('1', 'Chłopiec'),
        ('2', 'Dziewczynka')
    )
    count = 0
    # group = ()
    # groups = Groups.objects.all()
    # for group in groups:
    #     count += 1
    #     group = group + ((f'{count}', group.address),)
    first_name = forms.CharField(max_length=128)
    last_name = forms.CharField(max_length=128)
    # group_name = forms.ChoiceField(choices=group)
    gender = forms.ChoiceField(choices=genders)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'gender']


class TeacherRegisterForm(UserCreationForm):

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2']
