from django import forms
from .models import Post, Director
from groups.models import Groups


class CustomModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, group):
        """ Customises the labels for checkboxes"""
        return f"{group.name}"


class PostAddForm(forms.ModelForm):

    def __init__(self, *args, current_user=None, **kwargs):
        self.director = kwargs.pop("director", None)
        self.employee = kwargs.pop("employee", None)
        super().__init__(*args, **kwargs)
        if current_user is not None:
            if current_user.get_user_permissions() == {'director.is_director'}:
                self.fields['group'].queryset = current_user.director.groups_set.filter(is_active=True)

            elif current_user.get_user_permissions() == {'teacher.is_teacher'}:
                self.fields['group'].queryset = current_user.employee.principal.first().groups_set.filter(is_active=True)

        elif self.director is not None:
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
