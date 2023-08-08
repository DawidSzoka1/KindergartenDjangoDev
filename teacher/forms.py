from django import forms
from .models import Employee
from director.models import Director


# class TeacherUpdateForm(forms.ModelForm):
#
#     def __init__(self, *args, current_user=None, **kwargs):
#         super().__init__(*args, **kwargs)
#         if current_user is not None:
#             self.fields['group'].queryset = Director.objects.get(user=current_user.id).groups_set.all()
#
#     class Meta:
#         model = Teacher
#         fields = ['role', '', 'salary']
#         widgets = {'group': forms.Select}
