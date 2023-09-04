from django import forms
from .models import ContactModel, Director


class ContactAddForm(forms.ModelForm):
    class Meta:
        model = ContactModel
        fields = '__all__'

        labels = {
            'phone': 'NR KONTAKTOWY:',
            'email_address': 'E-MAIL KONTAKTOWY:',
            'localization': 'LOKALIZACJA:',

        }


class DirectorUpdateForm(forms.ModelForm):
    class Meta:
        model = Director
        fields = '__all__'

        labels = {
            "first_name": 'Imię:',
            'last_name': 'Nazwisko:',
            "gender": 'Płeć'
        }
