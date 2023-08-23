from django import forms
from .models import ParentA


class ParentUpdateForm(forms.ModelForm):
    class Meta:
        model = ParentA
        fields = '__all__'

        labels = {
            'first_name': "Imie:",
            'last_name': "Nazwisko:",
            'city': 'Miasto:',
            'address': 'Adres:',
            'zip_code': 'Kod pocztowy:',
            'phone': 'Numer telefonu:',
            'gender': 'Płeć'
        }
