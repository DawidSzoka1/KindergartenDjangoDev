from django import forms
from .models import Kid, Groups, Director, PaymentPlan, Meals


class KidAddForm(forms.ModelForm):

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['group'].queryset = Director.objects.filter(user=user).first().groups.all()

    class Meta:
        model = Kid
        fields = ['first_name', 'last_name', 'group', 'gender', 'start', 'end', 'payment_plan', 'kid_meals']
        widgets = {
            'start': forms.DateInput(attrs={'type': 'date'}),
            'end': forms.DateInput(attrs={'type': 'date'}),

        }


class PaymentPlanForm(forms.ModelForm):

    class Meta:
        model = PaymentPlan
        fields = '__all__'


class MealsForm(forms.ModelForm):

    class Meta:
        model = Meals
        fields = '__all__'


class GroupsForm(forms.ModelForm):

    class Meta:
        model = Groups
        fields = '__all__'
