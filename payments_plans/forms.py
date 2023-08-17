from django import forms
from .models import PaymentPlan


class PaymentPlanForm(forms.ModelForm):
    class Meta:
        model = PaymentPlan
        fields = '__all__'
        widgets = {'principal': forms.HiddenInput}

        labels = {
            'name': 'Nazwa:',
            'price': 'Kwota za miesiąc:'
        }
