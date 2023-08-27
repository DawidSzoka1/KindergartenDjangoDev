from django import forms
from .models import Post, Director


class CustomModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, group):
        """ Customises the labels for checkboxes"""
        return f"{group.name}"


class PostAddForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.director = kwargs.pop("director", None)
        self.employee = kwargs.pop("employee", None)
        super().__init__(*args, **kwargs)
        if self.director is not None:
            self.fields['group'].queryset = self.director.groups_set.filter(is_active=True)
        elif self.employee is not None:
            self.fields['group'].queryset = self.employee.principal.first().groups_set.filter(is_active=True)

    class Meta:
        model = Post
        fields = "__all__"

        widgets = {
            'author': forms.HiddenInput,
            'director': forms.HiddenInput,
            'content': forms.Textarea(attrs={'placeholder': 'Zacznij wpis..'})
        }

        labels = {
            'content': ''
        }

    group = CustomModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        label=''
    )
