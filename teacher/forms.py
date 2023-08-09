from django import forms
from .models import Employee
from director.models import Director


class TeacherUpdateForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'



