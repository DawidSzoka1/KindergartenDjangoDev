from django import forms
from .models import ParentA
from children.models import Kid
from director.models import Director, User
from director.forms import KindergartenBaseForm


class ParentUpdateForm(KindergartenBaseForm):
    class Meta:
        model = ParentA
        exclude = ['user', 'kindergarten', 'kids', 'principal']

        labels = {
            'first_name': "Imie:",
            'last_name': "Nazwisko:",
            'city': 'Miasto:',
            'address': 'Adres:',
            'zip_code': 'Kod pocztowy:',
            'phone': 'Numer telefonu:',
            'gender': 'Płeć'
        }

    def clean_kids(self):
        # Usuwamy walidację pola kids z formularza, aby nie zgłaszał błędu 'To pole jest wymagane'
        # W Django 4+ to jest najlepszy sposób na pominięcie walidacji ManyToMany bez blank=True
        return self.cleaned_data.get('kids', [])

        # (Opcjonalnie: możesz też nadpisać clean_phone, jeśli chcesz by phone było opcjonalne w formularzu bez zmiany modelu)

    def clean_phone(self):
        phone_data = self.cleaned_data.get('phone')
        if not phone_data:
            # Akceptujemy, że jest puste, jeśli nie było w ogóle wysłane.
            return None
        # Jeśli zostało wysłane, walidacja i tak działa
        return phone_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tutaj możesz dodać specyficzne klasy CSS dla pól
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-input-styled'})

    def clean_kids(self):
        # Zwracamy istniejący zestaw children, co usunie walidację "To pole jest wymagane".
        # Ponieważ w widoku użyjemy save(commit=False), to co zwróci clean_kids nie zostanie zapisane
        # do bazy, ale pozwala formularzowi przejść walidację.
        return self.instance.kids.all()
    def clean_principal(self):
        return self.instance.principal.all()