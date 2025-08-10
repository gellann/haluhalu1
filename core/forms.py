from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import *

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'profile_pic', 'is_seller')

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            base = "w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-200 placeholder-gray-400"
            self.fields["username"].widget.attrs.update({"class": base, "placeholder": "Enter your name"})
            self.fields["email"].widget.attrs.update(
                {"class": base, "placeholder": "Enter your email", "type": "email"})
            self.fields["password1"].widget.attrs.update({"class": base, "placeholder": "Create password"})
            self.fields["password2"].widget.attrs.update({"class": base, "placeholder": "Confirm password"})

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'profile_pic', 'is_seller', 'is_active', 'is_staff','is_superuser', 'groups', 'user_permissions')