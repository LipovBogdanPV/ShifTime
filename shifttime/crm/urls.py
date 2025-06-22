from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("success/", views.success, name="success"),
    path("Add_product/", views.add_product, name="add_product"),
    path("Order_list/", views.order_list, name="order_list"),
]