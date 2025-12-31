from django import forms
from .models import Post, Director
from groups.models import Groups
from director.forms import KindergartenBaseForm

class CustomModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, group):
        """ Customises the labels for checkboxes"""
        return f"{group.name}"


class PostAddForm(KindergartenBaseForm):
    group = forms.ModelMultipleChoiceField(
        queryset=Groups.objects.none(), # Queryset zostanie ustawiony w __init__ przez bazowy form
        widget=forms.CheckboxSelectMultiple(),
        required=False, # To pozwala na nie wybranie żadnej grupy
        label='Grupy docelowe'
    )
    class Meta:
        model = Post
        # Wybieramy konkretne pola, aby zachować kontrolę nad kolejnością
        fields = ['title', 'event_date', 'category', 'content', 'group', 'author', 'is_active']

        widgets = {
            'author': forms.HiddenInput(),
            'is_active': forms.HiddenInput(),
            'title': forms.TextInput(attrs={
                'placeholder': 'np. Wycieczka do zoo',
                'class': 'form-control'
            }),
            'event_date': forms.DateInput(
                format='%Y-%m-%d',attrs={
                'type': 'date', # Wywołuje systemowy kalendarz w przeglądarce
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={
                'placeholder': 'Opisz szczegóły wydarzenia...',
                'rows': 4,
                'class': 'form-control'
            }),
            # Widget CheckboxSelectMultiple pozwoli nam na renderowanie siatki w HTML
            'group': forms.CheckboxSelectMultiple(),
        }

        labels = {
            'title': 'Tytuł wydarzenia',
            'event_date': 'Data wydarzenia',
            'category': 'Typ ogłoszenia',
            'content': 'Treść wiadomości',
            'group': 'Grupy docelowe',
        }

    def __init__(self, *args, **kwargs):
        employee_profile = kwargs.pop('employee', None)
        role = kwargs.get('role')

        super().__init__(*args, **kwargs)

        # Upewniamy się, że pole nie jest wymagane
        self.fields['group'].required = False

        # Specyficzna logika dla nauczyciela
        if role == 'teacher' and employee_profile:
            if hasattr(employee_profile, 'group') and employee_profile.group:
                self.fields['group'].queryset = self.fields['group'].queryset.filter(id=employee_profile.group.id)

