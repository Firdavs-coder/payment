# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('create-checkout-session/<str:price_id>', views.create_checkout_session, name='create_checkout_session'),
    path('success/', views.success, name='success'),
    path('', views.home, name='home'),
    path('cancel/', views.cancel, name='cancel'),
    path('stripe-webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('cancel-subscription/<str:subscription_id>/', views.cancel_subscription, name='cancel_subscription'),
]