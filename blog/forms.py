from django import forms


class PostCreateForm(forms.Form):
    title = forms.CharField(max_length=128)
    contex = forms.Textarea()
    image = forms.ImageField(required=False)
