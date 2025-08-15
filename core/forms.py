# core/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, Product, Message # Import Message model


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'profile_pic')

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
        fields = ('username', 'email', 'profile_pic','is_active', 'is_staff', 'is_superuser', 'groups',
                  'user_permissions')


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'description', 'price', 'category', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe your product...'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Electronics, Fashion'}),
        }

# NEW: MessageForm
class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['receiver', 'subject', 'body'] # 'sender' and 'sent_at' will be set automatically
        widgets = {
            'receiver': forms.Select(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-200'}),
            'subject': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-200', 'placeholder': 'Subject'}),
            'body': forms.Textarea(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-200', 'rows': 6, 'placeholder': 'Your message here...'}),
        }

    def __init__(self, *args, **kwargs):
        # Optional: Pass 'user' to the form to exclude self from receiver list
        self.request_user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.request_user:
            # Exclude the current user from the list of possible receivers
            self.fields['receiver'].queryset = CustomUser.objects.exclude(pk=self.request_user.pk)
        else:
            self.fields['receiver'].queryset = CustomUser.objects.all()