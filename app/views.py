from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .models import Product, Subscribe, Invoice

import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(request, price_id: str):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url='http://localhost:8000/success/',
            cancel_url='http://localhost:8000/cancel/',
            metadata={
                'user_id': request.user.id,
                'price_id': price_id,
            }
        )
        return HttpResponseRedirect(session.url)
    except Exception as e:
        return JsonResponse({'error': str(e)})


def cancel_subscription(request, subscription_id):
    try:
        stripe.Subscription.delete(subscription_id)
        Subscribe.objects.get(stripe_subscription_id=subscription_id).delete()

        return redirect('home')
    except Subscribe.DoesNotExist:
        return JsonResponse({"error": "Subscription not found."}, status=404)
    except stripe.error.StripeError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": "An unexpected error occurred."}, status=500)

def home(request):
    products = Product.objects.all()
    subscribes = Subscribe.objects.filter(user=request.user)

    filteredData = []

    for product in list(products):
        data = {}
        data['title'] = product.title
        data['price'] = product.price
        data['price_id'] = product.price_id
        data['isSubscribed'] = False

        for subscribe in list(subscribes):
            if product == subscribe.product:
                data['isSubscribed'] = True
                data['subscription_id'] = subscribe.stripe_subscription_id
                break
        
        filteredData.append(data)

    context = {
        "filteredData": filteredData,
    }
    return render(request, 'index.html', context)

def success(request):
    return render(request, 'success.html')

def cancel(request):
    return render(request, 'cancel.html')

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    endpoint_secret = 'whsec_...'

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    event_type = event['type']
    event_data: dict = event['data']['object']

    if event_type == 'checkout.session.completed':
        metadata: dict = event_data.get("metadata")

        user_id = int(metadata.get('user_id', 0))
        price_id = metadata.get('price_id', 0)

        subscription_id = event_data.get('subscription')
        customer_id = event_data.get('customer')

        user = User.objects.get(id=user_id)
        product = Product.objects.get(price_id=price_id)

        subscription, created = Subscribe.objects.update_or_create(
            user=user,
            product=product,
            defaults = {
                'stripe_subscription_id': subscription_id,
                'customer_id': customer_id,
            }
        )

    elif event_type == 'invoice.payment_succeeded':
        customer_id = event_data.get('customer')
        stripe_subscription_id = event_data.get('subscription')
        invoice_id = event_data.get('id')
        hosted_invoice_url = event_data.get('hosted_invoice_url')
        invoice_pdf = event_data.get('invoice_pdf')

        subscribe = Subscribe.objects.get(stripe_subscription_id=stripe_subscription_id)

        Invoice.objects.create(
            user=subscribe.user,
            subscribe=subscribe,
            hosted_invoice_url=hosted_invoice_url,
            invoice_id=invoice_id,
            invoice_pdf=invoice_pdf,
            customer_id=customer_id,
            stripe_subscription_id=stripe_subscription_id
        )
        
        print("Invoice created!")

    elif event_type == 'invoice.payment_failed':
        invoice = event_data
        print(f"Invoice {invoice['id']} payment failed.")
        
        customer_id = invoice.get('customer')
        print(f"Customer {customer_id} failed to pay invoice.")
        
    elif event_type == 'customer.subscription.deleted':
        subscription = event_data
        print(f"Subscription {subscription['id']} cancelled.")
        
        user_id = subscription.get('customer')
        print(f"User {user_id} cancelled their subscription.")
        
    else:
        print(f"Unhandled event type {event_type}")

    return JsonResponse({'status': 'success'}, status=200)

