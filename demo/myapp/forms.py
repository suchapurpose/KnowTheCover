from django import forms
from .models import Collection

class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ['title', 'cover_image', 'release_info']