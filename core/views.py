# core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.db.models import Max, F

from .forms import CustomUserCreationForm, ProductForm, MessageForm
from .models import CustomUser, Product, Message


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
    success_url = reverse_lazy('product_list')
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


# REVISED: Messaging Views

# View for user's inbox (now displays conversation heads)
class InboxView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'core/inbox.html'
    context_object_name = 'conversations'
    paginate_by = 10
    login_url = 'login'

    def get_queryset(self):
        # We need to find the *unique conversation starters* that the current user is involved in.
        # Then, for each unique conversation starter, we display the LATEST message in that conversation.

        # 1. Get all messages where the current user is either sender or receiver
        user_messages = Message.objects.filter(Q(sender=self.request.user) | Q(receiver=self.request.user))

        # 2. Get the IDs of all conversation starters for these messages.
        # This includes messages that are their own conversation_starter (where conversation_starter is null,
        # so we use their own PK) and messages that refer to another message as their starter.

        # Use a subquery to find the latest message for each distinct conversation starter
        # (or for messages that are their own starter).

        # Get the IDs of the conversation starters for messages involving the user
        conversation_starters_involved = user_messages.values_list('conversation_starter', flat=True).distinct()

        # Also include messages that are their own starters (where conversation_starter is None)
        messages_as_starters = user_messages.filter(conversation_starter__isnull=True).values_list('pk', flat=True)

        # Combine and remove duplicates, also filter out None if any
        all_relevant_starter_pks = set(list(conversation_starters_involved) + list(messages_as_starters))
        all_relevant_starter_pks.discard(None)  # Remove None if present

        # Now, for each unique conversation starter PK, find the LATEST message in that thread
        # that the current user is involved in.
        latest_messages_per_conversation = []
        for starter_pk in all_relevant_starter_pks:
            # Get the actual conversation starter message object (this is what we link to)
            starter_message = get_object_or_404(Message, pk=starter_pk)

            # Find the very last message in this specific conversation thread involving the current user
            last_message_in_thread = Message.objects.filter(
                Q(conversation_starter=starter_message) | Q(pk=starter_message.pk),  # Get all messages in this thread
                Q(sender=self.request.user) | Q(receiver=self.request.user)
                # Ensure the current user is part of this specific message
            ).order_by('-sent_at').first()

            if last_message_in_thread:
                latest_messages_per_conversation.append(last_message_in_thread)

        # Sort these conversation summary messages by their sent_at in descending order
        # so the most recently active conversations appear at the top of the inbox.
        return sorted(latest_messages_per_conversation, key=lambda x: x.sent_at, reverse=True)


# View for user's sent messages (should function similarly to inbox, showing threads)
class SentMessagesView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'core/sent.html'
    context_object_name = 'conversations'
    paginate_by = 10
    login_url = 'login'

    def get_queryset(self):
        # Get all messages where the current user is the sender
        user_sent_messages = Message.objects.filter(sender=self.request.user)

        # Get the IDs of all conversation starters for these sent messages
        conversation_starters_involved = user_sent_messages.values_list('conversation_starter', flat=True).distinct()
        messages_as_starters = user_sent_messages.filter(conversation_starter__isnull=True).values_list('pk', flat=True)

        all_relevant_starter_pks = set(list(conversation_starters_involved) + list(messages_as_starters))
        all_relevant_starter_pks.discard(None)

        latest_messages_per_conversation = []
        for starter_pk in all_relevant_starter_pks:
            starter_message = get_object_or_404(Message, pk=starter_pk)

            # Find the very last message in this specific conversation thread
            # The user might not be the sender of the very last message, but they initiated or participated.
            last_message_in_thread = Message.objects.filter(
                Q(conversation_starter=starter_message) | Q(pk=starter_message.pk),
                Q(sender=self.request.user) | Q(receiver=self.request.user)
                # Still show conversations where user is a participant
            ).order_by('-sent_at').first()

            if last_message_in_thread:
                latest_messages_per_conversation.append(last_message_in_thread)

        return sorted(latest_messages_per_conversation, key=lambda x: x.sent_at, reverse=True)


# SendMessageView remains the same as before, handling parent_message and conversation_starter assignment correctly.
class SendMessageView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'core/send_message.html'
    success_url = reverse_lazy('inbox')
    login_url = 'login'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        recipient_id = self.kwargs.get('recipient_pk')
        parent_message_id = self.kwargs.get('parent_pk')

        if recipient_id:
            try:
                recipient_user = CustomUser.objects.get(pk=recipient_id)
                initial['receiver'] = recipient_user
            except CustomUser.DoesNotExist:
                messages.error(self.request, "Recipient user not found.")

        if parent_message_id:
            parent_message = get_object_or_404(Message, pk=parent_message_id)
            initial[
                'receiver'] = parent_message.sender if self.request.user == parent_message.receiver else parent_message.receiver
            initial['subject'] = f"Re: {parent_message.subject}" if not parent_message.subject.startswith(
                'Re:') else parent_message.subject
        return initial

    def form_valid(self, form):
        form.instance.sender = self.request.user

        parent_message_id = self.kwargs.get('parent_pk')
        if parent_message_id:
            parent_message = get_object_or_404(Message, pk=parent_message_id)
            form.instance.parent_message = parent_message
            form.instance.conversation_starter = parent_message.conversation_starter or parent_message
        else:
            form.instance.conversation_starter = None

        response = super().form_valid(form)

        if not form.instance.conversation_starter:
            form.instance.conversation_starter = form.instance
            form.instance.save()

        messages.success(self.request, "Message sent successfully!")
        return response


# MessageDetailView also remains the same and correctly fetches the full conversation.
class MessageDetailView(LoginRequiredMixin, DetailView):
    model = Message
    template_name = 'core/message_detail.html'
    context_object_name = 'current_message'
    login_url = 'login'

    def get_queryset(self):
        return Message.objects.filter(Q(sender=self.request.user) | Q(receiver=self.request.user))

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_message = context['current_message']

        conversation_starter = current_message.conversation_starter or current_message

        conversation_messages = Message.objects.filter(
            Q(conversation_starter=conversation_starter) | Q(pk=conversation_starter.pk)
        ).order_by('sent_at')

        context['conversation_messages'] = conversation_messages

        all_participants = set()
        for msg in conversation_messages:
            all_participants.add(msg.sender)
            all_participants.add(msg.receiver)

        other_participant = None
        for participant in all_participants:
            if participant != self.request.user:
                other_participant = participant
                break

        context['other_participant'] = other_participant

        for msg in conversation_messages:
            if self.request.user == msg.receiver and not msg.is_read:
                msg.is_read = True
                msg.save()

        return context