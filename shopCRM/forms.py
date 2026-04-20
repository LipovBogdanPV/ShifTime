from django import forms
from .models import Category, Client, MessageTemplate, Order, Product, User
from django.contrib.auth.models import Group, Permission

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'middle_name', 'email', 'phone', 'photo', 'card_number', 'groups']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Додаємо класи CSS для гарного вигляду
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'crm-input'})

class UserCreateForm(forms.ModelForm):
    # Додаємо поле пароля окремо, щоб воно було замасковане (password widget)
    password = forms.CharField(label="Тимчасовий пароль", widget=forms.PasswordInput(attrs={'class': 'crm-input'}))

    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name', 'middle_name', 'email', 'phone', 'photo', 'card_number', 'groups']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'password':
                self.fields[field].widget.attrs.update({'class': 'crm-input'})

class RoleForm(forms.ModelForm):
    # Виводимо дозволи як список чекбоксів
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.exclude(content_type__app_label__in=['admin', 'sessions', 'contenttypes', 'auth']),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'perm-checkbox'}),
        required=False,
        label="Дозволи"
    )

    class Meta:
        model = Group
        fields = ['name', 'permissions']
        labels = {'name': 'Назва ролі'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'crm-input'})

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'parent']
        widgets = {
            'parent': forms.Select(attrs={'class': 'form-control'}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'size', 'cost_price', 'drop_price', 'selling_price']
        # Можна додати класи для CSS, якщо потрібно
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['last_name', 'first_name', 'middle_name', 'phone', 'email', 'region', 'city', 'post_department']

class OrderMetaForm(forms.ModelForm):
    """Форма для основних полів замовлення (без товарів)"""
    class Meta:
        model = Order
        fields = ['platform', 'delivery_service', 'prepayment_amount', 'price_selling', 'engraving_description', 'customer_request']


class MessageTemplateForm(forms.ModelForm):
    class Meta:
        model = MessageTemplate
        fields = ['name', 'is_active', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 16}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'crm-input'})

