from django.contrib import admin
from .models import Product, Subscribe, Invoice

# Register your models here.
admin.site.register(Product)
admin.site.register(Subscribe)
admin.site.register(Invoice)