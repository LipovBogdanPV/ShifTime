from django.shortcuts import render, redirect
from .models import Product, OrderItem
from .forms import OrderForm


def index(request):
    products = Product.objects.all()
    form = OrderForm()
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save()
            selected = request.POST.getlist("product")
            for name in selected:
                try:
                    product = Product.objects.get(name=name.split()[0])
                    OrderItem.objects.create(order=order, product=product)
                except Product.DoesNotExist:
                    pass
            return redirect("success")
    return render(request, "crm/index.html", {"products": products, "form": form})


def success(request):
    return render(request, "crm/success.html")

def add_product(request):
    return render(request, "crm/Add_product.html")

def order_list(request):
    return render(request, "crm/Order_list.html")