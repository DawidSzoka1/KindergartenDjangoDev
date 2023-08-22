from django import forms
from .models import ContactModel


class ContactAddForm(forms.ModelForm):
    class Meta:
        model = ContactModel
        fields = '__all__'

        labels = {
            'phone': 'NR KONTAKTOWY:',
            'email_address': 'E-MAIL KONTAKTOWY:',
            'localization': 'LOKALIZACJA:',
        }
