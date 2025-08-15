# core/urls.py

from django.urls import path
from . import views
from .views import (
    ProductListView, ProductDetailView, ProductCreateView, ProductUpdateView, ProductDeleteView,
    InboxView, SentMessagesView, SendMessageView, MessageDetailView,
    delete_conversation_view
)

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('', views.base, name='base'),

    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('products/<int:pk>/edit/', ProductUpdateView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),
    path('products/add/', ProductCreateView.as_view(), name='product_add'),
    path('products/category/<str:category_name>/', ProductListView.as_view(), name='category_list'),

    # Messaging URLs
    path('messages/inbox/', InboxView.as_view(), name='inbox'),
    path('messages/sent/', SentMessagesView.as_view(), name='sent_messages'),
    path('messages/send/', SendMessageView.as_view(), name='message_send'),
    path('messages/send/<int:recipient_pk>/', SendMessageView.as_view(), name='message_send_to_user'),
    path('messages/reply/<int:parent_pk>/', SendMessageView.as_view(), name='message_reply'),
    path('messages/<int:pk>/', MessageDetailView.as_view(), name='message_detail'),

    path('messages/<int:pk>/delete/', views.delete_conversation_view, name='delete_conversation'),
]