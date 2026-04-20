from email.headerregistry import Group

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Category, Order, Client, OrderItem, Product, SiteSettings, User

# Спробуємо максимально явно прописати всі поля
class MyUserAdmin(UserAdmin):
    model = User
    
    # Стовпці, які ви бачите у загальному списку користувачів
    list_display = ['username', 'email', 'phone', 'role', 'is_staff']
    
    # Це налаштування розбиває сторінку редагування на блоки
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Особиста інформація', {'fields': ('first_name', 'last_name', 'middle_name', 'email', 'phone', 'photo')}),
        ('Банківські дані', {'fields': ('card_number',)}),
        ('Роль та доступ', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важливі дати', {'fields': ('last_login', 'date_joined')}),
    )

# Важливо: якщо ви бачите помилку "AlreadyRegistered", 
# розкоментуйте наступний рядок:
# admin.site.unregister(User)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent') # Показує батьківську категорію в списку

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'selling_price') # Показує категорію та ціну в списку

# Реєструємо твою кастомну модель
admin.site.register(User, UserAdmin)
admin.site.register(SiteSettings)
admin.site.register(Client)
admin.site.register(Order)
admin.site.register(OrderItem)

# Додамо перевірку в консоль (ви побачите це в терміналі при перезавантаженні)
print("Адмінка для User успішно завантажена!")