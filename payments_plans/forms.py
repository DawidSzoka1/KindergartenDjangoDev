# payments_plans/forms.py
from django import forms
from .models import PaymentPlan

class PaymentPlanForm(forms.ModelForm):
    class Meta:
        model = PaymentPlan
        fields = ['name', 'description', 'price', 'frequency', 'discount_info', 'principal', 'is_active', 'is_archived']
        widgets = {
            'principal': forms.HiddenInput(),
            'is_active': forms.HiddenInput(),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Opisz co obejmuje ten plan...'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'name': 'Nazwa Planu',
            'price': 'Kwota (zł)',
            'frequency': 'Częstotliwość opłat',
            'description': 'Opis planu',
            'discount_info': 'Informacje o zniżkach',
        }