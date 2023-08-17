from django import forms
from .models import Groups
from director.models import Director


class GroupsForm(forms.ModelForm):
    class Meta:
        model = Groups
        fields = '__all__'
        widgets = {
            'principal': forms.HiddenInput,
        }
        labels = {
            'name': 'Nazwa:',
            'capacity': 'Pojemność:'
        }

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if current_user is not None:
            self.fields['photo'] = forms.ModelChoiceField(
                queryset=Director.objects.get(user=current_user.id).groupphotos_set.filter(is_active=True))
