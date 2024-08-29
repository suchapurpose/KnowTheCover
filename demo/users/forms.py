from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput(), label="Confirm Password")
    class Meta:
        model = User
        fields = ['username', 'password1', 'confirm_password']
        label_suffix = '' 
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        confirm_password = cleaned_data.get("confirm_password")

        if password1 != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data