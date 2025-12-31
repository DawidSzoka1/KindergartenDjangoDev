# payments_plans/forms.py
from django import forms
from .models import PaymentPlan
from director.forms import KindergartenBaseForm


class PaymentPlanForm(KindergartenBaseForm):
    class Meta:
        model = PaymentPlan
        exclude = ['kindergarten', 'is_active', 'is_archived']
        widgets = {
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

    def __init__(self, *args, **kwargs):
        # Pobieramy k_id przekazane z widoku (get_form_kwargs)
        self.active_principal_id = kwargs.pop('active_principal_id', None)
        super().__init__(*args, **kwargs)
