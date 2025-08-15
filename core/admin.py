# core/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import CustomUser, Product, Message

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser

    list_display = ['username', 'email', 'is_staff']

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('profile_pic',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('profile_pic', )}),
    )


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Product)
admin.site.register(Message)