from django import forms
from .models import Groups
from director.models import Director
from director.forms import KindergartenBaseForm
from children.models import Kid
from teacher.models import Employee


class GroupsForm(KindergartenBaseForm):
    class Meta:
        model = Groups
        exclude = ['principal', 'kindergarten', 'is_active']
        labels = {
            'name': 'Nazwa:',
            'capacity': 'Pojemność:',
            'yearbook': "Rocznik:"
        }

    def __init__(self, *args, current_user=None, **kwargs):
        active_principal_id = kwargs.get('active_principal_id')
        super().__init__(*args, **kwargs)

        if active_principal_id:
            from director.models import GroupPhotos
            # Filtrujemy ikony po placówce, nie po dyrektorze
            self.fields['photo'].queryset = GroupPhotos.objects.filter(
                kindergarten_id=active_principal_id,
                is_active=True
            )


# W pliku Twojej_Aplikacji/forms.py
class AssignKidToGroupForm(forms.Form): # Tutaj może być zwykły forms.Form, jeśli tylko przypisujesz
    kid_to_assign = forms.ModelChoiceField(
        queryset=Kid.objects.none(),
        label="Wybierz dziecko do przypisania",
        required=True,
        widget=forms.Select(attrs={'class': 'js-select2-kid'})
    )

    def __init__(self, *args, **kwargs):
        group_pk = kwargs.pop('group_pk', None)
        k_id = kwargs.pop('active_principal_id', None)
        super().__init__(*args, **kwargs)

        if k_id and group_pk:
            # Filtrujemy dzieci należące do PLACÓWKI
            self.fields['kid_to_assign'].queryset = Kid.objects.filter(
                kindergarten_id=k_id,
                is_active=True
            ).exclude(
                group__pk=group_pk
            ).order_by('last_name', 'first_name')

class AssignTeachersForm(forms.Form):
    teachers_to_assign = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.none(),
        label="Dostępni Nauczyciele",
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, **kwargs):
        group_pk = kwargs.pop('group_pk', None)
        k_id = kwargs.pop('active_principal_id', None)
        super().__init__(*args, **kwargs)

        if k_id and group_pk:
            self.fields['teachers_to_assign'].queryset = Employee.objects.filter(
                kindergarten_id=k_id,
                is_active=True
            ).exclude(
                group__pk=group_pk
            ).order_by('last_name', 'first_name')