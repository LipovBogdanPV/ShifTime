from django import forms
from .models import Order, Customer

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone']

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['product', 'source']

class OrderForm(forms.Form):
    name = forms.CharField(label='Імʼя', max_length=100)
    phone = forms.CharField(label='Телефон', max_length=20)
    product = forms.CharField(label='Продукт', max_length=100)
    source = forms.CharField(label='Джерело', max_length=50)
