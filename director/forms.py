from django import forms
from .models import ContactModel, Director


class ContactAddForm(forms.ModelForm):
    class Meta:
        model = ContactModel
        exclude = ('director',)  # Ukrywamy dyrektora, przypiszemy go automatycznie

        labels = {
            'phone': 'Numer telefonu:',
            'email_address': 'E-mail kontaktowy:',
            'address': 'Ulica i numer:',
            'zip_code': 'Kod pocztowy:',
            'city': 'Miasto:',
            'office_hours': 'Godziny pracy biura:',
            'website_url': 'Strona internetowa (URL):',
            'additional_info': 'Dodatkowe informacje:',
        }
        widgets = {
            'additional_info': forms.Textarea(attrs={'rows': 3}),
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
