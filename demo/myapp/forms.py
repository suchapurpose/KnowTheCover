from django import forms
from django.utils.safestring import mark_safe
from .models import Collection

class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ['title']
        labels = {
            'title': mark_safe(''),
        }
