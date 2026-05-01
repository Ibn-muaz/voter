from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import INECUser


class INECUserCreationForm(UserCreationForm):
    """
    Form for creating new INEC users.
    """
    class Meta:
        model = INECUser
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'state', 'lga', 'employee_id')


class INECUserChangeForm(UserChangeForm):
    """
    Form for updating INEC users.
    """
    class Meta:
        model = INECUser
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'state', 'lga', 'employee_id', 'is_active_officer')


class LoginForm(forms.Form):
    """
    Login form for INEC officials.
    """
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username or Employee ID'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )