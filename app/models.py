from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Product(models.Model):
    title = models.CharField(max_length=200)
    price_id = models.CharField(max_length=200)
    price = models.IntegerField(default=0)

    def __str__(self):
        return self.title

class Subscribe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    customer_id = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return str(self.user) + " " + str(self.product)
    

class Invoice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscribe = models.ForeignKey(Subscribe, on_delete=models.CASCADE)
    hosted_invoice_url = models.CharField(max_length=9863)
    invoice_pdf = models.CharField(max_length=9863)
    invoice_id = models.CharField(max_length=255)
    date = models.DateField(auto_now_add=True)
    stripe_subscription_id = models.CharField(max_length=255)
    customer_id = models.CharField(max_length=255)

    def __str__(self):
        return f"Invoice: {self.subscribe} - {self.user}"

