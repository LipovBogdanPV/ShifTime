from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group, Permission
from django.conf import settings
from .models import AdExpense, Category, Client, FinanceConfig, MessageTemplate, Order, Product, SiteSettings, User, UserPayrollProfile, OrderItem
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from .forms import CategoryForm, MessageTemplateForm, ProductForm, RoleForm, UserCreateForm, UserEditForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, F, Sum
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from datetime import date, timedelta
from calendar import monthrange
from decimal import Decimal, InvalidOperation
import json
import requests
# Create your views here.
def login_view(request):
    # Якщо користувач уже в системі — відправляємо його на дашборд
    if request.user.is_authenticated:
        return redirect('dashboard')
    crm_name = SiteSettings.objects.filter(key='crm_name').first()
    context = {'crm_name': crm_name.value if crm_name else "CRM SHOP"}
    
    if request.method == 'POST':
        # Проста логіка для прикладу, краще використовувати Django Forms
        u = request.POST.get('username')  # змінив на email
        p = request.POST.get('password')
        user = authenticate(username=u, password=p)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            context['error'] = "Невірний логін або пароль"
            
    return render(request, 'shopCRM/login.html', context)

@login_required
def dashboard_view(request):
    crm_name = SiteSettings.objects.filter(key='crm_name').first()
    return render(request, 'shopCRM/dashboard.html', {
        'crm_name': crm_name.value if crm_name else "CRM SHOP"
    })

''' Приклад "AJAX" контенту
@login_required
def content_orders(request):
    return render(request, 'shopCRM/partials/orders.html')'''

def logout_user(request):
    logout(request)
    return redirect('login')

@login_required
def content_dashboard(request):
    return render(request, 'shopCRM/partials/content_dashboard.html')

@login_required
def content_analytics(request):
    return render(request, 'shopCRM/partials/analytics.html')


@login_required
def content_templates(request):
    templates = MessageTemplate.objects.all()
    return render(request, 'shopCRM/partials/templates.html', {'templates': templates})


def _parse_iso_date(value, fallback):
    try:
        if not value:
            return fallback
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return fallback


def _resolve_finance_period(period, reference_date):
    period = (period or 'month').lower()
    if period == 'day':
        return reference_date, reference_date, 'day'

    if period == 'quarter':
        quarter_index = (reference_date.month - 1) // 3
        start_month = quarter_index * 3 + 1
        start = date(reference_date.year, start_month, 1)
        end_month = start_month + 2
        end = date(reference_date.year, end_month, monthrange(reference_date.year, end_month)[1])
        return start, end, 'quarter'

    start = reference_date.replace(day=1)
    end = reference_date.replace(day=monthrange(reference_date.year, reference_date.month)[1])
    return start, end, 'month'


def _safe_sum(queryset, field_name):
    value = queryset.aggregate(total=Sum(field_name)).get('total')
    return value if value is not None else Decimal('0')


def _get_finance_config():
    config = FinanceConfig.objects.order_by('-id').first()
    if config:
        return config
    return FinanceConfig.objects.create()


def _get_or_create_payroll_profile(user, config):
    profile = getattr(user, 'payroll_profile', None)
    if profile:
        return profile

    return UserPayrollProfile.objects.create(
        user=user,
        hourly_rate=config.manager_hourly_rate,
        hours_per_day=config.manager_hours_per_day,
        monday_hours=config.manager_hours_per_day,
        tuesday_hours=config.manager_hours_per_day,
        wednesday_hours=config.manager_hours_per_day,
        thursday_hours=config.manager_hours_per_day,
        friday_hours=config.manager_hours_per_day,
        saturday_hours=Decimal('0'),
        sunday_hours=Decimal('0'),
        commission_percent=config.manager_commission_percent,
        include_in_payroll=True,
    )


def _calculate_scheduled_hours(profile, start_date, end_date):
    weekday_hours = {
        0: profile.monday_hours,
        1: profile.tuesday_hours,
        2: profile.wednesday_hours,
        3: profile.thursday_hours,
        4: profile.friday_hours,
        5: profile.saturday_hours,
        6: profile.sunday_hours,
    }

    total = Decimal('0')
    current = start_date
    while current <= end_date:
        total += Decimal(str(weekday_hours.get(current.weekday(), 0)))
        current += timedelta(days=1)

    return total


@login_required
def content_finance(request):
    reference_date = _parse_iso_date(request.GET.get('date'), date.today())
    start_date, end_date, period = _resolve_finance_period(request.GET.get('period'), reference_date)
    selected_statuses = request.GET.getlist('status')
    if not selected_statuses:
        selected_statuses = ['received']

    period_orders = Order.objects.select_related('manager').filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    )

    orders = period_orders.filter(status__in=selected_statuses)

    config = _get_finance_config()
    ad_expenses_qs = AdExpense.objects.filter(spend_date__gte=start_date, spend_date__lte=end_date)

    revenue = _safe_sum(orders, 'price_selling')
    wholesale = _safe_sum(orders, 'price_wholesale')
    gross_profit = revenue - wholesale
    ad_expenses = _safe_sum(ad_expenses_qs, 'amount')

    days_count = (end_date - start_date).days + 1

    users = User.objects.filter(is_active=True).order_by('last_name', 'first_name', 'username').prefetch_related('groups')
    user_rows = []
    base_salary = Decimal('0')
    manager_commission = Decimal('0')
    manager_count = 0

    for user in users:
        profile = _get_or_create_payroll_profile(user, config)
        user_period_orders = period_orders.filter(manager_id=user.id)
        user_calc_orders = user_period_orders.filter(status__in=selected_statuses)

        user_revenue = _safe_sum(user_calc_orders, 'price_selling')
        salary = Decimal('0')
        commission = Decimal('0')
        scheduled_hours = _calculate_scheduled_hours(profile, start_date, end_date)

        if profile.include_in_payroll:
            salary = profile.hourly_rate * scheduled_hours
            commission = user_revenue * profile.commission_percent / Decimal('100')
            manager_count += 1

        base_salary += salary
        manager_commission += commission

        user_rows.append({
            'user': user,
            'profile': profile,
            'orders_all_count': user_period_orders.count(),
            'orders_success_count': user_period_orders.filter(status='received').count(),
            'orders_canceled_count': user_period_orders.filter(status='canceled').count(),
            'orders_in_transit_count': user_period_orders.filter(status='shipped').count(),
            'orders_not_sent_count': user_period_orders.filter(status__in=['manufacturing', 'packaging']).count(),
            'orders_not_received_count': user_period_orders.exclude(status__in=['received', 'canceled']).count(),
            'calc_orders_count': user_calc_orders.count(),
            'calc_revenue': user_revenue,
            'scheduled_hours': scheduled_hours,
            'salary': salary,
            'commission': commission,
            'total_pay': salary + commission,
        })

    fop_income_tax = revenue * config.fop_income_tax_percent / Decimal('100')

    if period == 'day':
        days_in_month = monthrange(start_date.year, start_date.month)[1]
        fop_fixed_tax = config.fop_fixed_tax_monthly / Decimal(days_in_month)
    elif period == 'quarter':
        fop_fixed_tax = config.fop_fixed_tax_monthly * Decimal('3')
    else:
        fop_fixed_tax = config.fop_fixed_tax_monthly

    total_expenses = wholesale + ad_expenses + base_salary + manager_commission + fop_income_tax + fop_fixed_tax
    net_profit = revenue - total_expenses

    return render(request, 'shopCRM/partials/finance.html', {
        'period': period,
        'reference_date': reference_date.isoformat(),
        'selected_statuses': selected_statuses,
        'status_choices': Order.STATUS_CHOICES,
        'start_date': start_date,
        'end_date': end_date,
        'orders_count': orders.count(),
        'period_orders_count': period_orders.count(),
        'manager_count': manager_count,
        'days_count': days_count,
        'revenue': revenue,
        'wholesale': wholesale,
        'gross_profit': gross_profit,
        'ad_expenses': ad_expenses,
        'base_salary': base_salary,
        'manager_commission': manager_commission,
        'fop_income_tax': fop_income_tax,
        'fop_fixed_tax': fop_fixed_tax,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'finance_config': config,
        'user_rows': user_rows,
        'ad_expenses_list': ad_expenses_qs.order_by('-spend_date', '-id')[:50],
    })


@login_required
@require_POST
def save_finance_config(request):
    config = _get_finance_config()

    config.manager_commission_percent = _parse_decimal(request.POST.get('manager_commission_percent'), default=str(config.manager_commission_percent))
    config.fop_fixed_tax_monthly = _parse_decimal(request.POST.get('fop_fixed_tax_monthly'), default=str(config.fop_fixed_tax_monthly))
    config.fop_income_tax_percent = _parse_decimal(request.POST.get('fop_income_tax_percent'), default=str(config.fop_income_tax_percent))
    config.save()

    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def add_ad_expense(request):
    spend_date = _parse_iso_date(request.POST.get('spend_date'), None)
    if spend_date is None:
        return JsonResponse({'status': 'error', 'message': 'Некоректна дата витрат'}, status=400)

    amount = _parse_decimal(request.POST.get('amount'), default='0')
    if amount <= 0:
        return JsonResponse({'status': 'error', 'message': 'Сума витрат має бути більшою за 0'}, status=400)

    AdExpense.objects.create(
        spend_date=spend_date,
        amount=amount,
        comment=(request.POST.get('comment') or '').strip(),
    )
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def delete_ad_expense(request, expense_id):
    expense = get_object_or_404(AdExpense, id=expense_id)
    expense.delete()
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def save_user_payroll_settings(request, user_id):
    user = get_object_or_404(User, id=user_id)
    config = _get_finance_config()
    profile = _get_or_create_payroll_profile(user, config)

    profile.hourly_rate = _parse_decimal(request.POST.get('hourly_rate'), default=str(profile.hourly_rate))
    profile.monday_hours = _parse_decimal(request.POST.get('monday_hours'), default=str(profile.monday_hours))
    profile.tuesday_hours = _parse_decimal(request.POST.get('tuesday_hours'), default=str(profile.tuesday_hours))
    profile.wednesday_hours = _parse_decimal(request.POST.get('wednesday_hours'), default=str(profile.wednesday_hours))
    profile.thursday_hours = _parse_decimal(request.POST.get('thursday_hours'), default=str(profile.thursday_hours))
    profile.friday_hours = _parse_decimal(request.POST.get('friday_hours'), default=str(profile.friday_hours))
    profile.saturday_hours = _parse_decimal(request.POST.get('saturday_hours'), default=str(profile.saturday_hours))
    profile.sunday_hours = _parse_decimal(request.POST.get('sunday_hours'), default=str(profile.sunday_hours))
    profile.hours_per_day = (
        profile.monday_hours
        + profile.tuesday_hours
        + profile.wednesday_hours
        + profile.thursday_hours
        + profile.friday_hours
    ) / Decimal('5')
    profile.commission_percent = _parse_decimal(request.POST.get('commission_percent'), default=str(profile.commission_percent))
    profile.include_in_payroll = (request.POST.get('include_in_payroll') == 'on')
    profile.save()

    return JsonResponse({'status': 'ok'})


@login_required
def get_message_template_form(request, template_id=None):
    instance = get_object_or_404(MessageTemplate, id=template_id) if template_id else None
    form = MessageTemplateForm(instance=instance)
    title = 'Редагувати шаблон' if template_id else 'Новий шаблон'

    html = render_to_string('shopCRM/partials/template_form.html', {
        'form': form,
        'template_id': template_id,
        'title': title,
    }, request=request)
    return JsonResponse({'html': html})


@login_required
@require_POST
def save_message_template_form(request, template_id=None):
    instance = get_object_or_404(MessageTemplate, id=template_id) if template_id else None
    form = MessageTemplateForm(request.POST, instance=instance)

    if form.is_valid():
        form.save()
        return JsonResponse({'status': 'ok'})

    return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)


@login_required
@require_POST
def delete_message_template(request, template_id):
    template = get_object_or_404(MessageTemplate, id=template_id)
    template.delete()
    return JsonResponse({'status': 'ok'})


def get_user_level(user):
    # 👑 Суперадмін має максимальний доступ
    if user.is_superuser:
        return 100
    # Беремо першу групу користувача, якщо вона є
    '''У реальному проекті краще мати чітку структуру ролей та їх рівнів
    group = user.groups.first()
    if group:
        # Ваші рівні доступу (налаштуйте під свої назви груп)
        if group.name == 'Адміністратор': return 50
        if group.name == 'Менеджер': return 20
        return 10
    return 0'''
    # Якщо у користувача кілька груп, можна визначити рівень за найвищим рівнем серед них (якщо у вас є така логіка) або просто за першою групою. Тут я використовую словник для гнучкості.
    levels = {
        'Адміністратор': 50,
        'Менеджер': 20,
        'Працівник': 10
    }

    user_levels = [
        levels.get(group.name, 0)
        for group in user.groups.all()
    ]

    return max(user_levels, default=0)

@login_required
def content_admins(request):
    current_level = get_user_level(request.user)
    # Додайте перевірку на None, щоб не було помилок для нових юзерів
    
    # Суперкористувач бачить усіх
    if request.user.is_superuser:
        users = User.objects.all()
    else:
        # Інші бачать себе + тих, у кого рівень менший
        # Це спрощений приклад, у реальному проекті краще фільтрувати за ID ролей
        # Використовуємо Q напряму, без префікса "models."
        users = User.objects.filter(is_superuser=False)
        # Додаткова фільтрація
        users = [u for u in users if (get_user_level(u) if u.groups.first() else 0) < current_level or u.id == request.user.id]

    roles = Group.objects.all()
    
    return render(request, 'shopCRM/partials/admins.html', {
        'users_list': users,
        'roles': roles,
        'current_level': current_level
    })

@login_required
def get_user_form(request, user_id=None):
    """Повертає HTML-форму для модалки"""
    if user_id:
        user_to_edit = get_object_or_404(User, id=user_id)
        # Перевірка прав: чи може поточний користувач редагувати цього юзера
        if not request.user.is_superuser and user_to_edit.id != request.user.id:
            if get_user_level(request.user) <= get_user_level(user_to_edit):
                return JsonResponse({'error': 'Недостатньо прав'}, status=403)
        form = UserEditForm(instance=user_to_edit)
    else:
        form = UserEditForm()

    html = render_to_string('shopCRM/partials/user_form.html', {'form': form, 'user_id': user_id}, request=request)
    return JsonResponse({'html': html})
# Збереження користувача (створення або редагування)
@login_required
def save_user_form(request, user_id=None):
    """Зберігає дані користувача"""
    if user_id:
        instance = get_object_or_404(User, id=user_id)
        form = UserEditForm(request.POST, request.FILES, instance=instance)
    else:
        form = UserEditForm(request.POST, request.FILES)

    if form.is_valid():
        user = form.save(commit=False)
        if not user_id:
            password = form.cleaned_data.get('password') # .get() безпечніше
            if password:
                user.set_password(password)
        user.save()
        form.save_m2m()
        # --- Робота з групами ---
        # Припускаємо, що у вашій формі поле для вибору ролі називається 'groups'
        '''role_id = request.POST.get('groups') 
        if role_id:
            user.groups.clear() # Очищаємо старі ролі
            user.groups.add(role_id) # Додаємо нову роль'''
        
        return JsonResponse({'status': 'ok'})
    
    return JsonResponse({'status': 'error', 'errors': form.errors})

# Видалення користувача (звільнення)
@login_required
@require_POST # Дозволяємо лише POST-запити для безпеки
def delete_user(request, user_id):
    user_to_delete = get_object_or_404(User, id=user_id)
    
    # Забороняємо видаляти самого себе
    if user_to_delete.id == request.user.id:
        return JsonResponse({'status': 'error', 'message': 'Ви не можете видалити власний акаунт!'}, status=400)
    
    # Перевірка прав (тільки суперюзер або адміністратор має право)
    if not request.user.is_superuser and get_user_level(request.user) < 50:
        return JsonResponse({'status': 'error', 'message': 'Недостатньо прав для видалення'}, status=403)
        
    user_to_delete.delete()
    return JsonResponse({'status': 'ok'})

@login_required
def get_user_form(request, user_id=None):
    if user_id:
        user_to_edit = get_object_or_404(User, id=user_id)
        form = UserEditForm(instance=user_to_edit)
        title = f"Редагування: {user_to_edit.username}"
    else:
        form = UserCreateForm() # Використовуємо форму створення
        title = "Додати нового співробітника"

    html = render_to_string('shopCRM/partials/user_form.html', {
        'form': form, 
        'user_id': user_id,
        'title': title
    }, request=request)
    return JsonResponse({'html': html})
# Збереження користувача (створення або редагування)
@login_required
def save_user_form(request, user_id=None):
    if user_id:
        instance = get_object_or_404(User, id=user_id)
        form = UserEditForm(request.POST, request.FILES, instance=instance)
    else:
        form = UserCreateForm(request.POST, request.FILES)

    if form.is_valid():
        user = form.save(commit=False)
        if not user_id:
            # Тільки для нового користувача встановлюємо пароль через спеціальний метод
            password = form.cleaned_data['password']
            user.set_password(password) 
        user.save()
        form.save_m2m()
        return JsonResponse({'status': 'ok'})
    
    return JsonResponse({'status': 'error', 'errors': form.errors})

# Словник для "людських" назв
PERMISSION_DESCRIPTIONS = {
    # =======================
    # Користувачі
    # =======================
    'add_user': 'Реєстрація нових співробітників та створення їм акаунтів.',
    'change_user': 'Редагування профілів, зміна номерів телефонів та призначення ролей.',
    'delete_user': 'Видалення співробітників із системи (звільнення).',
    'view_user': 'Перегляд списку колег та їхньої контактної інформації.',

    # =======================
    # Ролі (Групи)
    # =======================
    'add_group': 'Створення нових типів посад (наприклад, "Логіст", "Контент-менеджер").',
    'change_group': 'Зміна прав доступу для існуючих ролей.',
    'delete_group': 'Видалення ролі (всі користувачі цієї ролі втратять доступ).',
    'view_group': 'Перегляд переліку існуючих ролей.',

    # =======================
    # Permissions (системні дозволи)
    # =======================
    'add_permission': 'Створення нових системних дозволів (використовується рідко).',
    'change_permission': 'Редагування існуючих дозволів системи.',
    'delete_permission': 'Видалення дозволів (може вплинути на доступи ролей).',
    'view_permission': 'Перегляд списку всіх доступних дозволів.',

    # =======================
    # Налаштування сайту
    # =======================
    'add_sitesettings': 'Створення запису налаштувань системи (зазвичай один раз).',
    'change_sitesettings': 'Зміна назви CRM, логотипу та основних контактів фірми.',
    'delete_sitesettings': 'Видалення налаштувань сайту (не рекомендується).',
    'view_sitesettings': 'Перегляд поточних налаштувань системи.',
}

# Оновіть функцію get_role_form, щоб передавати опис дозволів у шаблон
# Ролі та їхні дозволи будуть відображатися з "людськими" назвами та описами у формі редагування ролей.
@login_required
def get_role_form(request, role_id=None):
    if role_id:
        role = get_object_or_404(Group, id=role_id)
        form = RoleForm(instance=role)
        title = f"Редагування ролі: {role.name}"
    else:
        form = RoleForm()
        title = "Створення нової ролі"

    html = render_to_string('shopCRM/partials/role_form.html', {
        'form': form, 
        'role_id': role_id,
        'title': title,
        'descriptions': PERMISSION_DESCRIPTIONS # Передаємо словник у шаблон
    }, request=request)
    return JsonResponse({'html': html})

# Функції для збереження та видалення ролей
@login_required
def save_role_form(request, role_id=None):
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Тільки суперзамін може керувати ролями'}, status=403)
        
    if role_id:
        instance = get_object_or_404(Group, id=role_id)
        form = RoleForm(request.POST, instance=instance)
    else:
        form = RoleForm(request.POST)

    if form.is_valid():
        form.save()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error', 'errors': form.errors})

@login_required
@require_POST
def delete_role(request, role_id):
    # Тільки суперкористувач може видаляти ролі
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Тільки суперкористувач може видаляти ролі!'}, status=403)
    
    role = get_object_or_404(Group, id=role_id)
    
    # Заборона видаляти системні ролі, якщо це потрібно (наприклад, Admin)
    # if role.name == 'Admin':
    #     return JsonResponse({'status': 'error', 'message': 'Цю роль не можна видалити'}, status=400)

    role.delete()
    return JsonResponse({'status': 'ok'})

# Приклад для категорій
@login_required
def manage_products(request):
    categories = Category.objects.all()
    # Отримуємо всі товари з категоріями одним запитом
    products = Product.objects.all().select_related('category')
    return render(request, 'shopCRM/partials/catalog.html', {'categories': categories,
        'products': products})

@login_required
def get_category_form(request, category_id=None):
    if category_id:
        category = get_object_or_404(Category, id=category_id)
        form = CategoryForm(instance=category)
        title = f"Редагування категорії: {category.name}"
    else:
        form = CategoryForm()
        title = "Створення нової категорії"
    return render(request, 'shopCRM/partials/form_categories.html', {'form': form, 'category_id': category_id, 'title': title})

@login_required
def save_category_form(request, category_id=None):
    # ПЕРЕВІРКА ДОСТУПУ
    if get_user_level(request.user) <= 20:
        raise PermissionDenied # Викине помилку 403, якщо рівень занизький
    instance = get_object_or_404(Category, id=category_id) if category_id else None
    form = CategoryForm(request.POST, instance=instance)
    if form.is_valid():
        form.save()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error', 'errors': form.errors})

# Приклад для товарів
''' 
@login_required
def manage_products(request):
    # Отримуємо всі товари з категоріями одним запитом
    products = Product.objects.all().select_related('products')
    return render(request, 'shopCRM/partials/categories.html', {
        'products': products
    })
'''
@login_required
def get_product_form(request, product_id=None):
    if product_id:
        product = get_object_or_404(Product, id=product_id)
        form = ProductForm(instance=product)
        title = f"Редагування товару: {product.name}"
    else:
        form = ProductForm()
        title = "Створення нового товару"
    return render(request, 'shopCRM/partials/form_product.html', {'form': form, 'product_id': product_id, 'title': title})
# Збереження товару (створення або редагування)
@login_required
def save_product_form(request, product_id=None):
    # ПЕРЕВІРКА ДОСТУПУ
    if get_user_level(request.user) <= 20:
        raise PermissionDenied # Викине помилку 403, якщо рівень занизький
    instance = get_object_or_404(Product, id=product_id) if product_id else None
    form = ProductForm(request.POST, request.FILES, instance=instance)
    if form.is_valid():
        form.save()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error', 'errors': form.errors})
# Видалення категорії та товару
@login_required
@require_POST  # Дозволяє тільки POST запити
def delete_category(request, pk):
    # ПЕРЕВІРКА ДОСТУПУ
    if get_user_level(request.user) <= 20:
        raise PermissionDenied # Викине помилку 403, якщо рівень занизький
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    return JsonResponse({'status': 'ok'})

@login_required
@require_POST
def delete_product(request, pk):
    # ПЕРЕВІРКА ДОСТУПУ
    if get_user_level(request.user) <= 20:
        raise PermissionDenied # Викине помилку 403, якщо рівень занизький
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return JsonResponse({'status': 'ok'})

def _current_month_range():
    today = date.today()
    start = today.replace(day=1)
    end = today.replace(day=monthrange(today.year, today.month)[1])
    return start, end


def _parse_decimal(value, default='0'):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def _manager_order_number(order):
    if not order.manager_id:
        return order.id

    return Order.objects.filter(
        manager_id=order.manager_id,
        created_at__lt=order.created_at,
    ).count() + 1


def _display_order_number_global(raw_value):
    value = str(raw_value or '').strip()
    if value.upper().startswith('ORD-'):
        return value[4:]
    return value


def _build_order_template_context(order):
    manager_order_no = _manager_order_number(order)
    separator = "* " * 19

    items_lines = []
    for item in order.items.select_related('product').all():
        product_name = item.product.name if item.product else 'Товар видалено'
        items_lines.append(f"• {product_name} ({item.quantity})")

    items_block = "\n".join(items_lines) if items_lines else "• Без товарів"

    fully_paid = order.prepayment_amount >= order.price_selling
    if fully_paid:
        customer_total_block = ""
    else:
        customer_total_block = (
            f"----------------------------------------\n"
            f"Вартість для клієнта: {order.price_selling} грн\n"
            f"(Наложка)\n"
        )

    ttn_block = f"ТТН - {order.ttn}" if order.ttn else "ТТН - Створіть самі"

    return {
        'manager_order_no': manager_order_no,
        'order_number_global': _display_order_number_global(order.order_number_global),
        'separator': separator,
        'items_block': items_block,
        'customer_total_block': customer_total_block,
        'drop_price': order.price_wholesale,
        'region': order.client.region,
        'city': order.client.city,
        'post_department': order.client.post_department,
        'recipient': f"{order.client.last_name} {order.client.first_name}".strip(),
        'phone': order.client.phone,
        'ttn_block': ttn_block,
        'customer_request': order.customer_request or '-',
    }


def _build_order_default_template(order):
    context = _build_order_template_context(order)
    return (
        f"ЗАМОВЛЕННЯ №{context['manager_order_no']}\n\n"
        f"{context['separator']}\n"
        f"{context['items_block']}\n\n"
        f"{context['customer_total_block']}"
        f"----------------------------------------\n"
        f"Дроп ціна {context['drop_price']} грн.\n"
        f"----------------------------------------\n\n"
        f"{context['region']},\n"
        f"{context['city']}\n"
        f"Нова пошта: {context['post_department']}\n"
        f"{context['recipient']}\n"
        f"{context['phone']}\n\n\n"
        f"{context['separator']}\n"
        f"{context['ttn_block']}\n"
        f"{context['separator']}\n\n"
        f"-----------------------------------------"
    )


def _build_order_message(order, template_obj=None):
    if not template_obj:
        return _build_order_default_template(order)

    context = _build_order_template_context(order)
    try:
        return template_obj.body.format(**context)
    except KeyError:
        return _build_order_default_template(order)


def _map_delivery_status_to_order_status(delivery_status_text):
    text = (delivery_status_text or '').lower()
    if 'отриман' in text or 'видан' in text:
        return 'received'
    if 'відмов' in text or 'повернен' in text:
        return 'canceled'
    if 'відправлен' in text or 'в дорозі' in text or 'прямує' in text:
        return 'shipped'
    return None


@login_required
def content_order_details(request):
    start_default, end_default = _current_month_range()

    start_date = request.GET.get('start_date') or start_default.isoformat()
    end_date = request.GET.get('end_date') or end_default.isoformat()
    manager_id = request.GET.get('manager_id', '')
    status = request.GET.get('status', '')
    q = request.GET.get('q', '').strip()

    orders = Order.objects.select_related('client', 'manager').prefetch_related('items__product').all()

    orders = orders.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)

    if manager_id:
        orders = orders.filter(manager_id=manager_id)

    if status:
        orders = orders.filter(status=status)

    if q:
        orders = orders.filter(
            Q(order_number_global__icontains=q)
            | Q(client__last_name__icontains=q)
            | Q(client__first_name__icontains=q)
            | Q(client__phone__icontains=q)
            | Q(ttn__icontains=q)
            | Q(client__city__icontains=q)
        )

    managers = User.objects.filter(order__isnull=False).distinct().order_by('last_name', 'first_name')

    return render(request, 'shopCRM/partials/order_details.html', {
        'orders': orders.order_by('-created_at'),
        'managers': managers,
        'status_choices': Order.STATUS_CHOICES,
        'selected': {
            'start_date': start_date,
            'end_date': end_date,
            'manager_id': manager_id,
            'status': status,
            'q': q,
        },
    })


@login_required
def get_order_edit_form(request, order_id):
    order = get_object_or_404(Order.objects.select_related('client').prefetch_related('items__product'), id=order_id)
    products = Product.objects.select_related('category').order_by('name')

    html = render_to_string('shopCRM/partials/order_edit_form.html', {
        'order': order,
        'products': products,
        'status_choices': Order.STATUS_CHOICES,
        'delivery_services': Order.DELIVERY_SERVICES,
        'platform_choices': Order.PLATFORM_CHOICES,
    }, request=request)
    return JsonResponse({'html': html})


@login_required
@require_POST
def save_order_edit_form(request, order_id):
    order = get_object_or_404(Order.objects.select_related('client').prefetch_related('items'), id=order_id)
    client = order.client

    client.last_name = request.POST.get('last_name', client.last_name)
    client.first_name = request.POST.get('first_name', client.first_name)
    client.middle_name = request.POST.get('middle_name', client.middle_name)
    client.phone = request.POST.get('phone', client.phone)
    client.email = request.POST.get('email', client.email)
    client.region = request.POST.get('region', client.region)
    client.city = request.POST.get('city', client.city)
    client.post_department = request.POST.get('post_department', client.post_department)
    client.save()

    order.status = request.POST.get('status', order.status)
    order.delivery_service = request.POST.get('delivery_service', order.delivery_service)
    order.platform = request.POST.get('platform', order.platform)
    order.ttn = request.POST.get('ttn', order.ttn)
    order.prepayment_amount = _parse_decimal(request.POST.get('prepayment_amount'), default=str(order.prepayment_amount))
    order.engraving_description = request.POST.get('engraving_description', order.engraving_description)
    order.customer_request = request.POST.get('customer_request', order.customer_request)

    product_ids = request.POST.getlist('item_product')
    quantities = request.POST.getlist('item_quantity')

    order.items.all().delete()

    total_selling = Decimal('0')
    total_wholesale = Decimal('0')

    for idx, product_id in enumerate(product_ids):
        if not product_id:
            continue
        quantity_raw = quantities[idx] if idx < len(quantities) else '1'
        try:
            quantity = max(1, int(quantity_raw))
        except (TypeError, ValueError):
            quantity = 1

        product = Product.objects.filter(id=product_id).first()
        if not product:
            continue

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price_at_moment=product.selling_price,
            cost_price=product.cost_price,
        )

        total_selling += product.selling_price * quantity
        total_wholesale += product.cost_price * quantity

    order.price_selling = total_selling
    order.price_wholesale = total_wholesale
    order.save()

    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def delete_order(request, order_id):
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Тільки суперкористувач може видаляти замовлення.'}, status=403)

    order = get_object_or_404(Order, id=order_id)
    order.delete()
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def track_order_ttn(request, order_id):
    order = get_object_or_404(Order.objects.select_related('client'), id=order_id)
    ttn = (request.POST.get('ttn') or order.ttn or '').strip()

    if not ttn:
        return JsonResponse({'status': 'error', 'message': 'Вкажіть ТТН'}, status=400)

    payload = {
        'apiKey': settings.NP_API_KEY,
        'modelName': 'TrackingDocument',
        'calledMethod': 'getStatusDocuments',
        'methodProperties': {
            'Documents': [
                {
                    'DocumentNumber': ttn,
                    'Phone': order.client.phone,
                }
            ]
        }
    }

    response = requests.post('https://api.novaposhta.ua/v2.0/json/', json=payload, timeout=20)
    data = response.json()

    if not data.get('success'):
        return JsonResponse({'status': 'error', 'message': ', '.join(data.get('errors', ['Помилка API Нової Пошти']))}, status=400)

    np_data = data.get('data', [])
    if not np_data:
        return JsonResponse({'status': 'error', 'message': 'Не знайдено даних за ТТН'}, status=404)

    delivery_status_text = np_data[0].get('Status', '')
    order.ttn = ttn
    order.delivery_status_text = delivery_status_text

    mapped = _map_delivery_status_to_order_status(delivery_status_text)
    if mapped:
        order.status = mapped

    order.save()

    return JsonResponse({
        'status': 'ok',
        'delivery_status_text': order.delivery_status_text,
        'order_status': order.status,
    })


@login_required
def get_order_telegram_form(request, order_id):
    order = get_object_or_404(Order.objects.select_related('client', 'manager').prefetch_related('items__product'), id=order_id)
    template_id = request.GET.get('template_id')
    template_obj = MessageTemplate.objects.filter(id=template_id, is_active=True).first() if template_id else None
    message_text = _build_order_message(order, template_obj)
    default_chat_id = SiteSettings.objects.filter(key='telegram_manager_chat_id').values_list('value', flat=True).first() or ''
    templates = MessageTemplate.objects.filter(is_active=True)

    html = render_to_string('shopCRM/partials/order_telegram_form.html', {
        'order': order,
        'message_text': message_text,
        'default_chat_id': default_chat_id,
        'templates': templates,
        'selected_template_id': template_obj.id if template_obj else '',
    }, request=request)

    return JsonResponse({'html': html})


@login_required
def get_order_template_preview(request, order_id):
    order = get_object_or_404(Order.objects.select_related('client', 'manager').prefetch_related('items__product'), id=order_id)
    template_id = request.GET.get('template_id')
    template_obj = MessageTemplate.objects.filter(id=template_id, is_active=True).first() if template_id else None
    return JsonResponse({'text': _build_order_message(order, template_obj)})


@login_required
@require_POST
def send_order_to_telegram(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    chat_id = request.POST.get('chat_id', '').strip()
    text = request.POST.get('message_text', '').strip()

    if not text:
        return JsonResponse({'status': 'error', 'message': 'Текст повідомлення порожній'}, status=400)

    token = SiteSettings.objects.filter(key='telegram_bot_token').values_list('value', flat=True).first()
    token = token or getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    chat_id = chat_id or SiteSettings.objects.filter(key='telegram_manager_chat_id').values_list('value', flat=True).first() or getattr(settings, 'TELEGRAM_MANAGER_CHAT_ID', '')

    if not token:
        return JsonResponse({'status': 'error', 'message': 'Не налаштовано telegram_bot_token'}, status=400)

    if not chat_id:
        return JsonResponse({'status': 'error', 'message': 'Не вказано chat_id для Telegram'}, status=400)

    telegram_url = f'https://api.telegram.org/bot{token}/sendMessage'
    response = requests.post(telegram_url, data={
        'chat_id': chat_id,
        'text': text,
    }, timeout=20)

    response_data = response.json()
    if not response.ok or not response_data.get('ok'):
        return JsonResponse({'status': 'error', 'message': 'Не вдалося надіслати в Telegram'}, status=400)

    order.status = 'manufacturing'
    order.save(update_fields=['status'])

    return JsonResponse({'status': 'ok'})

@login_required
def content_orders(request):
    # Отримуємо тільки кореневі категорії (ті, у кого немає батьківської)
    root_categories = Category.objects.filter(parent__isnull=True)
    return render(request, 'shopCRM/partials/orders.html', {
        'root_categories': root_categories
    })

@login_required
def get_catalog_data(request, category_id):
    try:
        current_category = Category.objects.get(id=category_id) # Отримуємо назву категорії для хлібних крихт
        """Повертає підкатегорії та товари для обраної категорії"""
        subcategories = Category.objects.filter(parent_id=category_id)
        products = Product.objects.filter(category_id=category_id)
        
        data = {
            'category_name': current_category.name,
            'categories': list(subcategories.values('id', 'name')),
            'products': list(products.values('id', 'name', 'selling_price', 'drop_price'))
        }
        return JsonResponse(data)
    except Exception as e:
        print(f"ERROR IN AJAX: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def create_order_ajax(request):
    """Фінальне збереження всього замовлення"""
    try:
        data = json.loads(request.body)
        client_data = data.get('client', {})
        order_data = data.get('order', {})

        client, created = Client.objects.get_or_create(
            phone=client_data.get('phone', ''),
            defaults={
                'last_name': client_data.get('last_name', ''),
                'first_name': client_data.get('first_name', ''),
                'middle_name': client_data.get('middle_name', ''),
                'email': client_data.get('email', ''),
                'region': client_data.get('region', ''),
                'city': client_data.get('city', ''),
                'post_department': client_data.get('post_department', '')
            }
        )

        order = Order.objects.create(
            client=client,
            manager=request.user,
            order_number_global='TEMP',
            platform=order_data.get('platform', 'instagram'),
            delivery_service=order_data.get('delivery_service', 'nova_poshta'),
            prepayment_amount=order_data.get('prepayment_amount', 0),
            price_selling=order_data.get('total_price', 0),
            engraving_description=order_data.get('engraving_description', ''),
            customer_request=order_data.get('customer_request', ''),
            price_wholesale=0
        )

        total_wholesale = 0
        for item in data.get('items', []):
            product = Product.objects.get(id=item['id'])
            quantity = int(item.get('quantity', 1))
            cost_price = product.cost_price
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price_at_moment=product.selling_price,
                cost_price=cost_price
            )
            total_wholesale += cost_price * quantity

        order.order_number_global = str(order.id)
        order.price_wholesale = total_wholesale
        order.save()

        return JsonResponse({'status': 'success', 'order_id': order.id})
    except Product.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Один з товарів не знайдений'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)