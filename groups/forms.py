from django import forms
from .models import Groups
from director.models import Director
from children.models import Kid
from teacher.models import Employee


class GroupsForm(forms.ModelForm):
    class Meta:
        model = Groups
        fields = '__all__'
        widgets = {
            'principal': forms.HiddenInput,
        }
        labels = {
            'name': 'Nazwa:',
            'capacity': 'Pojemność:',
            'yearbook': "Rocznik:"
        }

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if current_user is not None:
            self.fields['photo'] = forms.ModelChoiceField(
                queryset=Director.objects.get(user=current_user.id).groupphotos_set.filter(is_active=True))


# W pliku Twojej_Aplikacji/forms.py
class AssignKidToGroupForm(forms.Form):
    # Field do wyboru dziecka
    # QuerySet musi być ograniczony do dzieci Dyrektora, które NIE SĄ w tej grupie
    kid_to_assign = forms.ModelChoiceField(
        queryset=Kid.objects.none(),
        label="Wybierz dziecko do przypisania",
        required=True,
        # Możesz użyć Select2 w HTML/JS dla lepszego doświadczenia
        widget=forms.Select(attrs={'class': 'js-select2-kid'})
    )

    def __init__(self, *args, **kwargs):
        group_pk = kwargs.pop('group_pk', None)
        user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)

        if user and group_pk:
            # Ograniczamy listę do dzieci dyrektora, które obecnie nie są w tej grupie
            self.fields['kid_to_assign'].queryset = Kid.objects.filter(
                principal__user=user,
                is_active=True
            ).exclude(
                group__pk=group_pk
            ).order_by('last_name', 'first_name')


class AssignTeachersForm(forms.Form):
    teachers_to_assign = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.none(), # Wypełnione w __init__
        label="Dostępni Nauczyciele",
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, **kwargs):
        group_pk = kwargs.pop('group_pk', None)
        user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)

        if user and group_pk:
            # 1. Pobieramy ID dyrektora
            director = Director.objects.get(user=user)

            # 2. Ograniczamy listę do nauczycieli dyrektora, którzy NIE są w tej grupie
            self.fields['teachers_to_assign'].queryset = Employee.objects.filter(
                principal=director,
                is_active=True
            ).exclude(
                group__pk=group_pk
            ).order_by('last_name', 'first_name')