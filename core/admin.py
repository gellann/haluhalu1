# core/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import CustomUser, Product


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser

    list_display = ['username', 'email', 'is_seller', 'is_staff']

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('profile_pic', 'is_seller')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('profile_pic', 'is_seller')}),
    )


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Product)