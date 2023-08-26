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
        if self.director:
            self.fields['group'].queryset = self.director.groups_set.filter(is_active=True)
            self.fields['director'].initial = self.director
            self.fields['author'].initial = self.director.user
        elif self.employee:
            self.fields['group'].queryset = self.employee.principal.first().groups_set.filter(is_active=True)
            self.fields['director'].initial = self.employee.principal.first()
            self.fields['author'].initial = self.employee.user

    class Meta:
        model = Post
        fields = "__all__"

        widgets = {
            'author': forms.HiddenInput,
            'principal': forms.HiddenInput,
            'director': forms.HiddenInput,

        }

    group = CustomModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        label=''
    )
