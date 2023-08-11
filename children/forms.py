from django import forms
from .models import Kid, Groups, Director, PaymentPlan, Meals


class KidAddForm(forms.ModelForm):

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if current_user is not None:
            self.fields['group'].queryset = Director.objects.get(user=current_user.id).groups_set.filter(is_active=True)
            self.fields['kid_meals'].queryset = Director.objects.get(user=current_user.id).meals_set.filter(
                is_active=True)
            self.fields['payment_plan'].queryset = Director.objects.get(user=current_user.id).paymentplan_set.filter(
                is_active=True)

    class Meta:
        model = Kid
        fields = ['first_name', 'last_name', 'group', 'gender', 'start', 'end', 'payment_plan', 'kid_meals',
                  'principal']

        widgets = {
            'start': forms.DateInput(attrs={'type': 'date'}),
            'end': forms.DateInput(attrs={'type': 'date'}),
            'principal': forms.HiddenInput,

        }


class ChangeKidInfoForm(forms.ModelForm):
    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if current_user is not None:
            self.fields['group'].queryset = Director.objects.get(user=current_user.id).groups.filter(is_active=True)
            self.fields['kid_meals'].queryset = Director.objects.get(user=current_user.id).meals.filter(is_active=True)
            self.fields['payment_plan'].queryset = Director.objects.get(user=current_user.id).payment_plan.filter(
                is_active=True)

    class Meta:
        model = Kid
        fields = ['first_name', 'last_name', 'group', 'gender', 'payment_plan', 'kid_meals', 'principal']
        widgets = {'principal': forms.HiddenInput}


class PaymentPlanForm(forms.ModelForm):
    class Meta:
        model = PaymentPlan
        fields = '__all__'
        widgets = {'principal': forms.HiddenInput}


class GroupsForm(forms.ModelForm):
    class Meta:
        model = Groups
        fields = '__all__'
        widgets = {
            'principal': forms.HiddenInput,
        }

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if current_user is not None:
            self.fields['photo'] = forms.ModelChoiceField(
                queryset=Director.objects.get(user=current_user.id).groupphotos_set.filter(is_active=True))
