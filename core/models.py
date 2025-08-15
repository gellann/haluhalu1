# core/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.urls import reverse


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

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'pk': self.pk})

# NEW: Message Model
class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-sent_at'] # Order messages by most recent first

    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username}: {self.subject}"

    def get_absolute_url(self):
        return reverse('message_detail', kwargs={'pk': self.pk})