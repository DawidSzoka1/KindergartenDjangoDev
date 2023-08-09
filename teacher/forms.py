from django import forms
from .models import Employee
from director.models import Director


class TeacherUpdateForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'

        labels = {
            'first_name': "Imie:",
            'last_name': "Nazwisko:",
            'city': 'Miasto:',
            'address': 'Adres:',
            'zip_code': 'Kod pocztowy:',
            'phone': 'Numer telefonu:'
                  }


