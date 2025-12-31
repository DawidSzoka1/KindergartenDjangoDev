from django import forms
from .models import Kid, Director
from director.forms import KindergartenBaseForm
from parent.models import ParentA
from groups.models import Groups
from payments_plans.models import PaymentPlan
from meals.models import Meals

class KidAddForm(KindergartenBaseForm):
    # Pole do wyboru wielu rodziców jednocześnie
    parents = forms.ModelMultipleChoiceField(
        queryset=ParentA.objects.none(),
        required=False,
        label="Rodzice / Opiekunowie",
        widget=forms.SelectMultiple(attrs={'class': 'js-select2 w-full'})
    )

    class Meta:
        model = Kid
        fields = ['first_name', 'last_name', 'group', 'gender', 'start', 'end', 'payment_plan', 'kid_meals', 'date_of_birth']
        widgets = {
            'start': forms.DateInput(attrs={'type': 'date'}),
            'end': forms.DateInput(attrs={'type': 'date'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        active_principal_id = kwargs.pop('active_principal_id', None)
        super().__init__(*args, **kwargs)
        if active_principal_id:
            # Filtrujemy dostępnych rodziców tylko z tej placówki
            self.fields['parents'].queryset = ParentA.objects.filter(
                kindergarten_id=active_principal_id
            ).select_related('user')

            # Filtrujemy pozostałe pola placówki
            self.fields['group'].queryset = Groups.objects.filter(kindergarten_id=active_principal_id, is_active=True)
            self.fields['kid_meals'].queryset = Meals.objects.filter(kindergarten_id=active_principal_id, is_active=True)
            self.fields['payment_plan'].queryset = PaymentPlan.objects.filter(kindergarten_id=active_principal_id, is_active=True)


class KidUpdateForm(KindergartenBaseForm):
    parents = forms.ModelMultipleChoiceField(
        queryset=ParentA.objects.none(),
        required=False,
        label="Przypisani rodzice",
        help_text="Możesz wybrać wielu. Przytrzymaj Ctrl (Cmd na Macu).",
        widget=forms.SelectMultiple(attrs={'class': 'js-select2-parents'})
    )

    class Meta:
        model = Kid
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender',
            'group', 'payment_plan', 'kid_meals',
            'start', 'end'
        ]
        widgets = {
            'start': forms.DateInput(attrs={'type': 'date'}),
            'end': forms.DateInput(attrs={'type': 'date'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        active_principal_id = kwargs.get('active_principal_id')
        super().__init__(*args, **kwargs)

        if active_principal_id:
            # Filtrowanie rodziców dostępnych w TEJ placówce
            self.fields['parents'].queryset = ParentA.objects.filter(
                kindergarten_id=active_principal_id
            ).select_related('user')

        # Ustawiamy aktualnie przypisanych rodziców jako zaznaczonych
        if self.instance and self.instance.pk:
            self.fields['parents'].initial = self.instance.parenta_set.all()