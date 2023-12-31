from django import forms
from .models import Kid, Director


class KidAddForm(forms.ModelForm):

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if current_user is not None:
            self.fields['group'].queryset = Director.objects.get(user=current_user.id).groups_set.filter(is_active=True)
            self.fields['kid_meals'].queryset = Director.objects.get(user=current_user.id).meals_set.filter(
                is_active=True)
            self.fields['payment_plan'].queryset = Director.objects.get(user=current_user.id).paymentplan_set.filter(
                is_active=True)

    class Meta:
        model = Kid
        fields = ['first_name', 'last_name', 'group', 'gender', 'start', 'end', 'payment_plan', 'kid_meals',
                  'principal', 'date_of_birth']

        widgets = {
            'start': forms.DateInput(format=('%Y-%m-%d'), attrs={'type': 'date'}),
            'end': forms.DateInput(format=('%Y-%m-%d'), attrs={'type': 'date'}),
            'date_of_birth': forms.DateInput(format=('%Y-%m-%d'), attrs={'type': 'date'}),
            'principal': forms.HiddenInput,

        }

        labels = {
            'first_name': 'Imię:',
            'last_name': 'Nazwisko:',
            'group': 'Grupa:',
            'gender': 'Płeć:',
            'start': 'Początek umowy:',
            'end': 'Koniec umowy:',
            'payment_plan': 'Plan płatniczy:',
            'kid_meals': 'Posiłek:',
            'date_of_birth': 'Data urodzenia'
        }
