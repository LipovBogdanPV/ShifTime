from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return self.name

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.CharField(max_length=255)
    source = models.CharField(max_length=50)  # Наприклад: 'Telegram', 'OLX', 'Prom'
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product} для {self.customer.name}"