from django import forms
from .models import Post, Director
from groups.models import Groups


class CustomModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, group):
        """ Customises the labels for checkboxes"""
        return f"{group.name}"


class PostAddForm(forms.ModelForm):
    class Meta:
        model = Post
        # Wybieramy konkretne pola, aby zachować kontrolę nad kolejnością
        fields = ['title', 'event_date', 'category', 'content', 'group', 'author', 'director', 'is_active']

        widgets = {
            'author': forms.HiddenInput(),
            'director': forms.HiddenInput(),
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
        # Wyciągamy obiekty dyrektora lub pracownika przekazane z widoku
        director = kwargs.pop("director", None)
        employee = kwargs.pop("employee", None)

        super().__init__(*args, **kwargs)

        # Logika filtrowania grup w zależności od tego, kto dodaje post
        if director:
            # Dyrektor widzi wszystkie aktywne grupy w swojej placówce
            self.fields['group'].queryset = Groups.objects.filter(
                principal=director,
                is_active=True
            ).order_by('name')

        elif employee:
            # Nauczyciel widzi tylko grupy, do których jest przypisany
            # Używamy employee.group, ponieważ model Employee ma relację do Groups
            self.fields['group'].queryset = Groups.objects.filter(
                id=employee.group.id,
                is_active=True
            ) if employee.group else Groups.objects.none()

        # Dodatkowa klasa dla etykiet grup, aby ułatwić stylowanie w Tailwind
        self.fields['group'].widget.attrs.update({'class': 'group-checkbox-input'})
