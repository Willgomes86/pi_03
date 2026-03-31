from django import forms
from .models import Familia


class FamiliaForm(forms.ModelForm):
    class Meta:
        model = Familia
        fields = "__all__"
