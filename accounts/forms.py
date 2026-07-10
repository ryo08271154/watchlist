from accounts.models import User
from django import forms
from django.contrib.auth.forms import UserCreationForm


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "nickname", "is_public"]


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "nickname", "is_public"]
