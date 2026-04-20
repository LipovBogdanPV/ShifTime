from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.db.models import Sum
# models.py

# Create your models here.
class User(AbstractUser):
    # ПІБ окремими полями для зручності пошуку
    middle_name = models.CharField("По батькові", max_length=150, blank=True)
    phone = models.CharField("Номер телефону", max_length=20, unique=True)
    email = models.EmailField("Email", unique=True, blank=False, null=False)
    
    # Фото з плейсхолдером (обробка логіки на фронтенді або через default)
    photo = models.ImageField("Фото", upload_to='user_photos/', null=True, blank=True)
    
    # Банківські дані
    card_number = models.CharField("Номер рахунку (карти)", max_length=25, blank=True)
    
    # Роль (зв'язок з вбудованими групами Django)
    '''role = models.ForeignKey(
        Group, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='user_roles',
        verbose_name="Роль"
    )'''
    REQUIRED_FIELDS = ['email']  # якщо логін по email

    def __str__(self):
        full_name = f"{self.last_name} {self.first_name} {self.middle_name}".strip()
        return full_name if full_name else self.username
    
class SiteSettings(models.Model):
    key = models.CharField("Ключ", max_length=50, unique=True)
    value = models.CharField("Значення", max_length=255)
    description = models.TextField("Опис", blank=True)

    class Meta:
        verbose_name = "Налаштування сайту"
        verbose_name_plural = "Налаштування сайту"

    def __str__(self):
        return self.key

# Допоміжна функція для отримання налаштувань у шаблонах
def get_setting(key, default="CRM SHOP"):
    try:
        return SiteSettings.objects.get(key=key).value
    except SiteSettings.DoesNotExist:
        return default

class Category(models.Model):
    name = models.CharField("Назва категорії", max_length=200)
    description = models.TextField("Опис (для розмірів/деталей)", blank=True, null=True)
    # Рекурсивний зв'язок для необмеженої вкладеності
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='subcategories',
        verbose_name="Батьківська категорія"
    )

    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"

    def __str__(self):
        # Допомагає бачити шлях до категорії (напр. Електроніка -> Телефони -> Чохли)
        full_path = [self.name]
        k = self.parent
        while k is not None:
            full_path.append(k.name)
            k = k.parent
        return ' -> '.join(full_path[::-1])

class Product(models.Model):
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='products',
        verbose_name="Категорія"
    )
    name = models.CharField("Назва товару", max_length=255)
    description = models.TextField("Опис товару", blank=True)
    size = models.CharField("Розмір (см, мм, шт)", max_length=100, blank=True)
    
    # Використовуємо DecimalField для фінансових даних (це обов'язково!)
    cost_price = models.DecimalField("Собівартість", max_digits=10, decimal_places=2)
    drop_price = models.DecimalField("Дроп ціна", max_digits=10, decimal_places=2)
    selling_price = models.DecimalField("Ціна продажу", max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товари"

    def __str__(self):
        return f"{self.name} ({self.selling_price} грн)"
    
class Client(models.Model):
    last_name = models.CharField("Прізвище", max_length=100)
    first_name = models.CharField("Ім'я", max_length=100)
    middle_name = models.CharField("По батькові", max_length=100, blank=True)
    phone = models.CharField("Телефон", max_length=20, unique=True)
    email = models.EmailField("Email", blank=True, null=True)
    region = models.CharField("Область", max_length=100)
    city = models.CharField("Місто", max_length=100)
    post_department = models.CharField("Відділення", max_length=255)

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.phone})"

class Order(models.Model):
    STATUS_CHOICES = [
        ('manufacturing', 'Виготовлення'),
        ('packaging', 'Комплектація'),
        ('shipped', 'Передано в службу доставки'),
        ('received', 'Отримано'),
        ('canceled', 'Скасовано'),
    ]
    
    DELIVERY_SERVICES = [
        ('nova_poshta', 'Нова Пошта'),
        ('ukr_poshta', 'Укрпошта'),
        ('self_pickup', 'Самовивіз'),
        ('other', 'Інша служба'),
    ]
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
        ('olx', 'OLX'),
        ('prom', 'Prom'),
        ('other', 'Інша'),
    ]

    client = models.ForeignKey(Client, on_delete=models.PROTECT, verbose_name="Клієнт")
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Менеджер")
    order_number_global = models.CharField("Глобальний №", max_length=50, unique=True)
    
    delivery_service = models.CharField("Служба доставки", max_length=20, choices=DELIVERY_SERVICES, default='nova_poshta')
    ttn = models.CharField("ТТН", max_length=50, blank=True, null=True)
    
    engraving_description = models.TextField("Опис гравіювання", blank=True)
    customer_request = models.TextField("Прохання клієнта", blank=True)
    
    price_wholesale = models.DecimalField("Оптова ціна", max_digits=10, decimal_places=2)
    price_selling = models.DecimalField("Ціна продажу", max_digits=10, decimal_places=2)
    prepayment_amount = models.DecimalField("Передоплата", max_digits=10, decimal_places=2, default=0)
    is_cod = models.BooleanField("Наложка", default=True)
    
    status = models.CharField("Статус", max_length=50, choices=STATUS_CHOICES, default='manufacturing')
    delivery_status_text = models.CharField("Статус доставки", max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField("Дата створення", auto_now_add=True)

    platform = models.CharField("Платформа", max_length=20, choices=PLATFORM_CHOICES, default='olx')

    # Додаємо метод для розрахунку прибутку (на основі товарів)
    @property
    def net_profit(self):
        # Рахуємо: (Ціна продажу) - (Сума всіх собівартостей товарів у цьому замовленні)
        total_cost = self.items.aggregate(
            total=Sum(models.F('cost_price') * models.F('quantity'))
        )['total'] or 0
        return self.price_selling - total_cost
    
    @property
    def remaining_to_pay(self):
        """Розрахунок залишку, який клієнт має доплатити"""
        remaining = self.price_selling - self.prepayment_amount
        return max(remaining, 0) # Повертає 0, якщо передоплата більша за ціну продажу
    
    def __str__(self):
        return f"Замовлення №{self.order_number_global} ({self.platform} - {self.client.first_name})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name="Замовлення")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name="Товар")
    quantity = models.PositiveIntegerField("Кількість", default=1)

    # Ціна продажу за 1 одиницю
    price_at_moment = models.DecimalField("Ціна продажу", max_digits=10, decimal_places=2)

    # СОБІВАРТІСТЬ товару (важливо для аналітики)
    cost_price = models.DecimalField("Собівартість (дроп)", max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.product.name} ({self.quantity} шт.)"


class MessageTemplate(models.Model):
    name = models.CharField("Назва шаблону", max_length=120, unique=True)
    body = models.TextField("Текст шаблону")
    is_active = models.BooleanField("Активний", default=True)
    created_at = models.DateTimeField("Створено", auto_now_add=True)
    updated_at = models.DateTimeField("Оновлено", auto_now=True)

    class Meta:
        verbose_name = "Шаблон повідомлення"
        verbose_name_plural = "Шаблони повідомлень"
        ordering = ["name"]

    def __str__(self):
        return self.name


class FinanceConfig(models.Model):
    manager_hourly_rate = models.DecimalField("Ставка менеджера за годину", max_digits=10, decimal_places=2, default=40)
    manager_hours_per_day = models.DecimalField("Годин на день", max_digits=5, decimal_places=2, default=8)
    manager_commission_percent = models.DecimalField("% менеджеру від замовлень", max_digits=5, decimal_places=2, default=5)
    fop_fixed_tax_monthly = models.DecimalField("Фіксований податок ФОП (місяць)", max_digits=10, decimal_places=2, default=0)
    fop_income_tax_percent = models.DecimalField("% податку від доходу", max_digits=5, decimal_places=2, default=5)
    updated_at = models.DateTimeField("Оновлено", auto_now=True)

    class Meta:
        verbose_name = "Фінансові налаштування"
        verbose_name_plural = "Фінансові налаштування"


class AdExpense(models.Model):
    spend_date = models.DateField("Дата")
    amount = models.DecimalField("Сума", max_digits=10, decimal_places=2)
    comment = models.CharField("Коментар", max_length=255, blank=True)
    created_at = models.DateTimeField("Створено", auto_now_add=True)

    class Meta:
        verbose_name = "Витрати на рекламу"
        verbose_name_plural = "Витрати на рекламу"
        ordering = ["-spend_date", "-id"]

    def __str__(self):
        return f"{self.spend_date}: {self.amount}"


class UserPayrollProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='payroll_profile', verbose_name='Користувач')
    hourly_rate = models.DecimalField("Ставка за годину", max_digits=10, decimal_places=2, default=40)
    hours_per_day = models.DecimalField("Годин на день", max_digits=5, decimal_places=2, default=8)
    monday_hours = models.DecimalField("Пн год", max_digits=5, decimal_places=2, default=8)
    tuesday_hours = models.DecimalField("Вт год", max_digits=5, decimal_places=2, default=8)
    wednesday_hours = models.DecimalField("Ср год", max_digits=5, decimal_places=2, default=8)
    thursday_hours = models.DecimalField("Чт год", max_digits=5, decimal_places=2, default=8)
    friday_hours = models.DecimalField("Пт год", max_digits=5, decimal_places=2, default=8)
    saturday_hours = models.DecimalField("Сб год", max_digits=5, decimal_places=2, default=0)
    sunday_hours = models.DecimalField("Нд год", max_digits=5, decimal_places=2, default=0)
    commission_percent = models.DecimalField("% від замовлень", max_digits=5, decimal_places=2, default=5)
    include_in_payroll = models.BooleanField("Враховувати в нарахуванні", default=True)
    updated_at = models.DateTimeField("Оновлено", auto_now=True)

    class Meta:
        verbose_name = "Налаштування оплати користувача"
        verbose_name_plural = "Налаштування оплат користувачів"

    def __str__(self):
        return f"Оплата: {self.user}"