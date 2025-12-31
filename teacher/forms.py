from django import forms
from .models import Employee
from director.models import Director
from director.forms import KindergartenBaseForm


class TeacherUpdateForm(KindergartenBaseForm):
    class Meta:
        model = Employee
        exclude = ['user', 'kindergarten', 'is_active', 'salary', 'role', 'group']

        labels = {
            'first_name': "Imie:",
            'last_name': "Nazwisko:",
            'city': 'Miasto:',
            'address': 'Adres:',
            'zip_code': 'Kod pocztowy:',
            'phone': 'Numer telefonu:',
            'gender': 'Płeć:'
                  }
    def __init__(self, *args, **kwargs):
        # Pobieramy k_id, aby w razie potrzeby przefiltrować grupy tylko dla tej placówki
        k_id = kwargs.get('active_principal_id')
        super().__init__(*args, **kwargs)

        if k_id:
            from children.models import Groups
            self.fields['group'].queryset = Groups.objects.filter(kindergarten_id=k_id, is_active=True)

