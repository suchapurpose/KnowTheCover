from django import forms
from django.utils.safestring import mark_safe
from .models import ReleaseList

class ReleaseListForm(forms.ModelForm):
    class Meta:
        model = ReleaseList
        fields = ['name']
        labels = {
            'name': mark_safe(''),
        }
