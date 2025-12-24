from django import forms
from .models import ParentA
from children.models import Kid
from director.models import Director, User


class ParentUpdateForm(forms.ModelForm):
    kids = forms.ModelMultipleChoiceField(
        queryset=Kid.objects.none(),
        required=False,
        widget=forms.HiddenInput()  # Używamy HiddenInput, aby nie wyświetlało się w szablonie
    )
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
        # Pobieramy instancję rodzica z argumentów (jeśli istnieje)
        parent_instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)

        if parent_instance:
            # Ustawiamy queryset pola 'kids' na tylko te dzieci,
            # które są już przypisane do edytowanego rodzica.
            self.fields['kids'].queryset = parent_instance.kids.all()
            self.fields['principal'].queryset = parent_instance.principal.all()
            self.initial['principal'] = parent_instance.principal.all()

            # Ustawienia dla pola 'user' (ustawiamy wartość początkową)
            self.fields['user'].queryset = User.objects.filter(pk=parent_instance.user.pk)
            self.initial['user'] = parent_instance.user
        else:
            # Jeśli to jest formularz do tworzenia (bez instancji), nadal ustawiamy pusty queryset
            self.fields['kids'].queryset = Kid.objects.none()

    def clean_kids(self):
        # Zwracamy istniejący zestaw children, co usunie walidację "To pole jest wymagane".
        # Ponieważ w widoku użyjemy save(commit=False), to co zwróci clean_kids nie zostanie zapisane
        # do bazy, ale pozwala formularzowi przejść walidację.
        return self.instance.kids.all()
    def clean_principal(self):
        return self.instance.principal.all()