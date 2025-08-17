# core/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator


class CustomUser(AbstractUser):
    profile_pic = models.ImageField(upload_to='profile_pics', null=True, blank=True)

    def __str__(self):
        return self.username


class Product(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    is_sold = models.BooleanField(default=False)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')
    posted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-posted_at']

    def __str__(self):
        return self.title

    # Corrected get_absolute_url method
    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'pk': self.pk})

    def average_rating(self):
        # Calculate the average rating from all related reviews
        return self.reviews.aggregate(models.Avg('rating'))['rating__avg']

    def review_count(self):
        # Count the number of reviews
        return self.reviews.count()

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    parent_message = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    conversation_starter = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='conversation_messages_set')

    is_deleted_by_sender = models.BooleanField(default=False)
    is_deleted_by_receiver = models.BooleanField(default=False)

    class Meta:
        ordering = ['sent_at']

    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username}: {self.subject}"

    def get_absolute_url(self):
        if self.conversation_starter:
            return reverse('message_detail', kwargs={'pk': self.conversation_starter.pk})
        return reverse('message_detail', kwargs={'pk': self.pk})

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Review for {self.product.title} by {self.author.username}'
