from django.contrib import admin
from .models import Customer, Order
from .google_sheets import GoogleSheet

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('product', 'customer', 'source', 'date_created')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        GoogleSheet(obj)

