from django.shortcuts import render, redirect
from .forms import CustomerForm, OrderForm
from .google_sheets import GoogleSheet
from datetime import datetime

SHEET_ID = '1dMKFRP6VJNh1mSJ4Ydy15uvaC7H8hcyyyubVF2tS64M'

def home(request):
    sheet = GoogleSheet(SHEET_ID)
    orders = sheet.read_all()
    return render(request, 'orders/home.html', {'orders': orders})

def create_order(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            sheet = GoogleSheet(SHEET_ID)
            sheet.append_order(
                name=data['name'],
                phone=data['phone'],
                product=data['product'],
                source=data['source'],
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            return redirect('order_success')
    else:
        form = OrderForm()
    return render(request, 'orders/create_order.html', {'form': form})

def order_success(request):
    return render(request, 'orders/success.html')