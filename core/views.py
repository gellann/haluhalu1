# core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
# Make sure to import UserPassesTestMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


from .forms import CustomUserCreationForm, ProductForm
from .models import CustomUser, Product


def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration completed.')
            return redirect('login')
        else:
            return render(
                request,
                'main/signup.html',
                {'form': form, 'error_message': 'Registration failed. Invalid information.'}
            )
    else:
        form = CustomUserCreationForm()
        return render(request, 'main/signup.html', {'form': form})

def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'You have successfully logged in as {user.username}.')
            next_url = request.GET.get('next') or 'base'
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'main/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required
def profile_view(request):
    return render(request, 'main/profile.html')


def base(request):
    return render(request, 'base.html')


# Category filter and pagination were added here
class ProductListView(ListView):
    model = Product
    template_name = 'core/product_list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        category_name = self.kwargs.get('category_name')
        if category_name:
            queryset = queryset.filter(category__iexact=category_name)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_category'] = self.kwargs.get('category_name')
        context['categories'] = Product.objects.values_list('category', flat=True).distinct()
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'core/product_detail.html'
    context_object_name = 'product'

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'core/product_form.html'
    success_url = reverse_lazy('product_list')
    login_url = 'login'
    redirect_field_name = 'next'

    def form_valid(self, form):
        form.instance.seller = self.request.user
        messages.success(self.request, "Product created successfully!")
        return super().form_valid(form)

# REVISED: ProductUpdateView to use UserPassesTestMixin
class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'core/product_form.html'
    context_object_name = 'product'
    login_url = 'login' # Ensure redirection to login if not authenticated

    def test_func(self):
        # Ensure only the seller can edit their product
        product = self.get_object()
        return self.request.user == product.seller

    def get_success_url(self):
        messages.success(self.request, "Product updated successfully!")
        return reverse_lazy('product_detail', kwargs={'pk': self.object.pk})

# REVISED: ProductDeleteView to use UserPassesTestMixin
class ProductDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Product
    template_name = 'core/product_confirm_delete.html'
    success_url = reverse_lazy('product_list')
    context_object_name = 'product'
    login_url = 'login' # Ensure redirection to login if not authenticated

    def test_func(self):
        # Ensure only the seller can delete their product
        product = self.get_object()
        return self.request.user == product.seller

    def form_valid(self, form):
        messages.success(self.request, "Product deleted successfully!")
        return super().form_valid(form)