from django import forms
from .models import ContactModel, Director


class KindergartenBaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Wyciągamy dane o placówce z kwargs
        self.active_principal_id = kwargs.pop('active_principal_id', None)
        self.current_user = kwargs.pop('current_user', None)

        super().__init__(*args, **kwargs)

        # Automatyczne filtrowanie wszystkich pól ForeignKey/ManyToManyField
        if self.active_principal_id:
            for field_name, field in self.fields.items():
                # Jeśli pole odnosi się do modelu powiązanego z placówką
                if hasattr(field, 'queryset') and hasattr(field.queryset.model, 'kindergarten'):
                    field.queryset = field.queryset.model.objects.filter(
                        kindergarten_id=self.active_principal_id,
                        is_active=True
                    )
                # Obsługa Twojego starego modelu principal
                elif hasattr(field, 'queryset') and hasattr(field.queryset.model, 'principal'):
                    field.queryset = field.queryset.model.objects.filter(
                        principal__id=self.active_principal_id,
                        is_active=True
                    )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if hasattr(instance, 'kindergarten_id') and self.active_principal_id:
            instance.kindergarten_id = self.active_principal_id

        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ContactAddForm(KindergartenBaseForm):
    kindergarten_name = forms.CharField(
        max_length=255,
        label='Nazwa placówki',
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Wpisz pełną nazwę przedszkola'})
    )

    class Meta:
        model = ContactModel
        # Wykluczamy stare powiązania
        exclude = ('director', 'kindergarten')

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

    def __init__(self, *args, **kwargs):
        # Pobieramy k_id przekazane z widoku
        active_principal_id = kwargs.get('active_principal_id')
        super().__init__(*args, **kwargs)

        # Jeśli edytujemy, ustawiamy nazwę placówki w polu tekstowym
        if self.instance and self.instance.pk and self.instance.kindergarten:
            self.fields['kindergarten_name'].initial = self.instance.kindergarten.name
        elif active_principal_id:
            # Jeśli tworzymy nowy kontakt, możemy pobrać nazwę placówki z obiektu Kindergarten
            from .models import Kindergarten
            k = Kindergarten.objects.filter(id=active_principal_id).first()
            if k:
                self.fields['kindergarten_name'].initial = k.name

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Aktualizujemy nazwę w głównym modelu przedszkola
        if instance.kindergarten:
            instance.kindergarten.name = self.cleaned_data['kindergarten_name']
            instance.kindergarten.save()
        if commit:
            instance.save()
        return instance


class DirectorUpdateForm(KindergartenBaseForm):
    class Meta:
        model = Director
        exclude = ['user', 'kindergarten', 'is_active']

        labels = {
            "first_name": 'Imię:',
            'last_name': 'Nazwisko:',
            "gender": 'Płeć'
        }
