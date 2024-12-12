from django import forms
from django.contrib.auth.forms import UserCreationForm
from meal_together.models.users import CustomUser
from django.contrib.auth.forms import AuthenticationForm

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['email','username', 'first_name', 'last_name', 'password1', 'password2']


class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"autofocus": True}))


class UserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username','first_name', 'last_name',]  # Możesz dodać inne pola, jeśli to konieczne
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }