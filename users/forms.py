from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget = forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username'
        })
        self.fields['email'].widget = forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email'
        })
        self.fields['password1'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
        self.fields['password2'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })

from django import forms
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
        })
    )

    def clean_email(self):
        # Get the email value entered by the user
        email = self.cleaned_data.get('email')

        # Check if the email exists in the database
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is not registered.')

        return email


class CustomUserLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password',
        })
    )

from django import forms
from django.core.exceptions import ValidationError

class EmailConfigurationForm(forms.Form):
    email_address = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        }),
        label="Email Address"
    )
    imap_server = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'IMAP server (e.g., imap.gmail.com)'
        }),
        label="IMAP Server"
    )
    smtp_server = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'SMTP server (e.g., smtp.gmail.com)'
        }),
        label="SMTP Server"
    )
    email_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email password'
        }),
        label="Email Password"
    )
    port_imap = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'IMAP port'}),
        initial=993, label="IMAP Port"
    )
    port_smtp = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'SMTP port'}),
        initial=587, label="SMTP Port"
    )

    def clean_email_address(self):
        email = self.cleaned_data.get('email_address')
        # Check if email is valid (you can add more checks if necessary)
        if not email:
            raise ValidationError("Email address is required")
        return email
