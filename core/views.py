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
from django.db.models import Max, F, Subquery, OuterRef
from django.http import HttpResponseForbidden
from .models import Product, Review


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()

        # Add the reviews for this product to the context
        context['reviews'] = product.reviews.all().order_by('-created_at')

        # Add the average rating and review count to the context
        context['average_rating'] = product.average_rating()
        context['review_count'] = product.review_count()

        return context


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

class InboxView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'core/inbox.html'
    context_object_name = 'conversations'
    paginate_by = 10
    login_url = 'login'

    def get_queryset(self):
        user = self.request.user

        # Get the IDs of all messages (sent or received by user) that are conversation starters,
        # and are not deleted by the current user.
        user_involved_conversation_starter_ids = Message.objects.filter(
            Q(sender=user, is_deleted_by_sender=False) | Q(receiver=user, is_deleted_by_receiver=False)
        ).values_list('conversation_starter__pk', flat=True) # Get starter PKs of all involved messages

        # Add the PKs of messages that are their own conversation starters (initial messages)
        user_involved_initial_message_ids = Message.objects.filter(
            Q(sender=user, is_deleted_by_sender=False, conversation_starter__isnull=True) |
            Q(receiver=user, is_deleted_by_receiver=False, conversation_starter__isnull=True)
        ).values_list('pk', flat=True)

        # Combine and get unique non-None starter PKs
        unique_starter_pks = set(list(user_involved_conversation_starter_ids) + list(user_involved_initial_message_ids))
        unique_starter_pks.discard(None) # Remove None if present

        # Fetch the actual conversation starter objects for these unique PKs
        # These are the "heads" of the conversations that should appear in the inbox
        # We also need to filter these starter messages themselves by their deletion status for the user
        valid_conversation_starters = Message.objects.filter(
            pk__in=list(unique_starter_pks)
        ).filter(
            Q(sender=user, is_deleted_by_sender=False) | Q(receiver=user, is_deleted_by_receiver=False)
        )

        # Now, for each valid conversation starter, find the LATEST message within that entire thread
        # that the current user is still able to see (i.e., not deleted by them).
        latest_messages_per_conversation = []
        for starter in valid_conversation_starters:
            latest_message_in_thread = Message.objects.filter(
                Q(conversation_starter=starter) | Q(pk=starter.pk) # All messages related to this starter
            ).filter(
                Q(sender=user, is_deleted_by_sender=False) | Q(receiver=user, is_deleted_by_receiver=False)
            ).order_by('-sent_at').first()

            if latest_message_in_thread:
                latest_messages_per_conversation.append(latest_message_in_thread)

        # Sort these summary messages by their sent_at in descending order
        return sorted(latest_messages_per_conversation, key=lambda x: x.sent_at, reverse=True)

# REMOVED: SentMessagesView is no longer needed

class SendMessageView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'core/send_message.html'
    success_url = reverse_lazy('inbox') # Always redirect to inbox
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
            initial['receiver'] = parent_message.sender if self.request.user == parent_message.receiver else parent_message.receiver
            initial['subject'] = f"Re: {parent_message.subject}" if not parent_message.subject.startswith('Re:') else parent_message.subject
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

class MessageDetailView(LoginRequiredMixin, DetailView):
    model = Message
    template_name = 'core/message_detail.html'
    context_object_name = 'current_message'
    login_url = 'login'

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(
            Q(sender=user, is_deleted_by_sender=False) | Q(receiver=user, is_deleted_by_receiver=False)
        )

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg)
        obj = get_object_or_404(self.get_queryset(), pk=pk)

        if obj.conversation_starter and obj.conversation_starter.pk != obj.pk:
            return get_object_or_404(self.get_queryset(), pk=obj.conversation_starter.pk)
        return obj


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        conversation_starter_message = context['current_message']

        conversation_messages = Message.objects.filter(
            Q(conversation_starter=conversation_starter_message) | Q(pk=conversation_starter_message.pk)
        ).filter(
            Q(sender=user, is_deleted_by_sender=False) | Q(receiver=user, is_deleted_by_receiver=False)
        ).order_by('sent_at')

        context['conversation_messages'] = conversation_messages

        all_participants = set()
        for msg in conversation_messages:
            all_participants.add(msg.sender)
            all_participants.add(msg.receiver)

        other_participant = None
        for participant in all_participants:
            if participant != user:
                other_participant = participant
                break

        context['other_participant'] = other_participant

        for msg in conversation_messages:
            if user == msg.receiver and not msg.is_read:
                msg.is_read = True
                msg.save()

        return context

@login_required
def delete_conversation_view(request, pk):
    """
    Handles soft deletion of an entire conversation for the current user.
    The PK passed is expected to be the conversation_starter's PK.
    """
    conversation_starter = get_object_or_404(Message, pk=pk)
    user = request.user

    if not (conversation_starter.sender == user or conversation_starter.receiver == user):
        messages.error(request, "You are not authorized to delete this conversation.")
        return redirect('inbox')

    messages_in_thread = Message.objects.filter(
        Q(conversation_starter=conversation_starter) | Q(pk=conversation_starter.pk)
    )

    for message in messages_in_thread:
        if message.sender == user:
            message.is_deleted_by_sender = True
        if message.receiver == user:
            message.is_deleted_by_receiver = True
        message.save()

    messages.success(request, "Conversation deleted successfully.")
    return redirect('inbox')


@login_required
def add_review(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        # Check if the user has already reviewed this product
        if Review.objects.filter(product=product, author=request.user).exists():
            return HttpResponseForbidden("You have already reviewed this product.")

        Review.objects.create(
            product=product,
            author=request.user,
            rating=rating,
            comment=comment
        )
        return redirect('product_detail', pk=pk)

    return redirect('product_detail', pk=pk)