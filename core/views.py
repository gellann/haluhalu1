# core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q # For searching, though not used in messaging yet


from .forms import CustomUserCreationForm, ProductForm, MessageForm # Import MessageForm
from .models import CustomUser, Product, Message # Import Message model


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

class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'core/product_form.html'
    context_object_name = 'product'
    success_url = reverse_lazy('product_list') # Changed to product_list for simplicity after edit, can be product_detail
    login_url = 'login'

    def test_func(self):
        product = self.get_object()
        return self.request.user == product.seller

    def get_success_url(self):
        messages.success(self.request, "Product updated successfully!")
        return reverse_lazy('product_detail', kwargs={'pk': self.object.pk})

class ProductDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Product
    template_name = 'core/product_confirm_delete.html'
    success_url = reverse_lazy('product_list')
    context_object_name = 'product'
    login_url = 'login'

    def test_func(self):
        product = self.get_object()
        return self.request.user == product.seller

    def form_valid(self, form):
        messages.success(self.request, "Product deleted successfully!")
        return super().form_valid(form)


# NEW: Messaging Views

# View for user's inbox (received messages)
class InboxView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'core/inbox.html'
    context_object_name = 'messages'
    paginate_by = 10
    login_url = 'login'

    def get_queryset(self):
        # Filter messages where the current user is the receiver
        return Message.objects.filter(receiver=self.request.user)

# View for user's sent messages
class SentMessagesView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'core/sent.html'
    context_object_name = 'messages'
    paginate_by = 10
    login_url = 'login'

    def get_queryset(self):
        # Filter messages where the current user is the sender
        return Message.objects.filter(sender=self.request.user)

# View for sending a new message
class SendMessageView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'core/send_message.html'
    success_url = reverse_lazy('sent_messages') # Redirect to sent messages after sending
    login_url = 'login'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user # Pass the current user to the form to filter receiver queryset
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # If a recipient_id is passed in the URL (e.g., from "Message Seller" button)
        recipient_id = self.kwargs.get('recipient_pk')
        if recipient_id:
            try:
                recipient_user = CustomUser.objects.get(pk=recipient_id)
                initial['receiver'] = recipient_user
            except CustomUser.DoesNotExist:
                messages.error(self.request, "Recipient user not found.")
                # Optionally redirect to a safer page if recipient not found
                # Or just let the form render with an empty receiver field
        return initial

    def form_valid(self, form):
        form.instance.sender = self.request.user # Set the sender to the current logged-in user
        messages.success(self.request, "Message sent successfully!")
        return super().form_valid(form)

# View for viewing a single message
class MessageDetailView(LoginRequiredMixin, DetailView):
    model = Message
    template_name = 'core/message_detail.html'
    context_object_name = 'message'
    login_url = 'login'

    def get_queryset(self):
        # Users can only view messages they sent or received
        return Message.objects.filter(Q(sender=self.request.user) | Q(receiver=self.request.user))

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        # Mark message as read if the current user is the receiver and it's unread
        if self.request.user == obj.receiver and not obj.is_read:
            obj.is_read = True
            obj.save()
        return obj