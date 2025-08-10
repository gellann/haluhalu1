from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import CustomUserCreationForm
from .models import CustomUser


def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  # create account but DO NOT log in
            messages.success(request, 'Registration completed.')
            return redirect('login')  # message will appear on login page
        else:
            messages.error(request, 'Registration failed. Invalid information.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'main/signup.html', {'form': form})


def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()  # AuthenticationForm already authenticated
            login(request, user)
            messages.success(request, f'You have successfully logged in as {user.username}.')
            # support ?next=... if present; otherwise go home
            next_url = request.GET.get('next') or 'base'
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'main/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')  # message will appear on login page


@login_required #
def profile_view(request):
    return render(request, 'main/profile.html')

def base(request):
    # homepage view (URL name should be 'base')
    return render(request, 'base.html')
