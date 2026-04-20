from django.contrib import admin
from django.urls import include, path
from shopCRM import views # Імпортуємо твій файл з логікою

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    # AJAX URL-адреси для динамічного завантаження контенту
    # замовлення та клієнти
    path('ajax/orders/', views.content_orders, name='content_orders'),
    path('ajax/get-catalog/<int:category_id>/', views.get_catalog_data, name='get_catalog_data'),

    path('ajax/create-order/', views.create_order_ajax, name='create_order_ajax'),
    path('ajax/contentdashboard/', views.content_dashboard, name='content_dashboard'),
    path('ajax/templates/', views.content_templates, name='content_templates'),
    path('ajax/finance/', views.content_finance, name='content_finance'),
    path('ajax/finance/config-save/', views.save_finance_config, name='save_finance_config'),
    path('ajax/finance/user-payroll-save/<int:user_id>/', views.save_user_payroll_settings, name='save_user_payroll_settings'),
    path('ajax/finance/ad-expense-add/', views.add_ad_expense, name='add_ad_expense'),
    path('ajax/finance/ad-expense-delete/<int:expense_id>/', views.delete_ad_expense, name='delete_ad_expense'),
    path('ajax/analytics/', views.content_analytics, name='content_analytics'),
    path('ajax/admins/', views.content_admins, name='content_admins'),
    path('ajax/user-form/', views.get_user_form, name='get_user_form_empty'),
    path('ajax/user-form/<int:user_id>/', views.get_user_form, name='get_user_form'),
    path('ajax/user-save/', views.save_user_form, name='save_user_empty'),
    path('ajax/user-save/<int:user_id>/', views.save_user_form, name='save_user'),
    path('ajax/user-delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('ajax/role-form/', views.get_role_form, name='get_role_form_empty'),
    path('ajax/role-form/<int:role_id>/', views.get_role_form, name='get_role_form'),
    path('ajax/role-save/', views.save_role_form, name='save_role_empty'),
    path('ajax/role-save/<int:role_id>/', views.save_role_form, name='save_role'),
    path('ajax/role-delete/<int:role_id>/', views.delete_role, name='delete_role'),
    # Категорії та продукти
    # КАТАЛОГ (Вкладки)
    path('ajax/manage_products/', views.manage_products, name='manage_products'),

    # КАТЕГОРІЇ (Отримати форму та Зберегти)
    # Додаємо url для створення нової категорії (без ID)
    path('ajax/category-form/', views.get_category_form, name='get_category_form_empty'),
    path('ajax/category-form/<int:category_id>/', views.get_category_form, name='get_category_form'),
    path('ajax/category-save/', views.save_category_form, name='save_category_empty'),
    path('ajax/category-save/<int:category_id>/', views.save_category_form, name='save_category'),

    # ТОВАРИ (Отримати форму та Зберегти)
    path('ajax/product-form/', views.get_product_form, name='get_product_form_empty'),
    path('ajax/product-form/<int:product_id>/', views.get_product_form, name='get_product_form'),
    path('ajax/product-save/', views.save_product_form, name='save_product_empty'),
    path('ajax/product-save/<int:product_id>/', views.save_product_form, name='save_product'),
    # Видалення категорій та продуктів
    path('delete-category/<int:pk>/', views.delete_category, name='delete_category'),
    path('delete-product/<int:pk>/', views.delete_product, name='delete_product'),
    path('ajax/content_order_details/', views.content_order_details, name='content_order_details'),
    path('ajax/order-edit-form/<int:order_id>/', views.get_order_edit_form, name='get_order_edit_form'),
    path('ajax/order-save/<int:order_id>/', views.save_order_edit_form, name='save_order_edit_form'),
    path('ajax/order-delete/<int:order_id>/', views.delete_order, name='delete_order'),
    path('ajax/order-track/<int:order_id>/', views.track_order_ttn, name='track_order_ttn'),
    path('ajax/order-telegram-form/<int:order_id>/', views.get_order_telegram_form, name='get_order_telegram_form'),
    path('ajax/order-template-preview/<int:order_id>/', views.get_order_template_preview, name='get_order_template_preview'),
    path('ajax/order-telegram-send/<int:order_id>/', views.send_order_to_telegram, name='send_order_to_telegram'),
    path('ajax/template-form/', views.get_message_template_form, name='get_message_template_form_empty'),
    path('ajax/template-form/<int:template_id>/', views.get_message_template_form, name='get_message_template_form'),
    path('ajax/template-save/', views.save_message_template_form, name='save_message_template_form_empty'),
    path('ajax/template-save/<int:template_id>/', views.save_message_template_form, name='save_message_template_form'),
    path('ajax/template-delete/<int:template_id>/', views.delete_message_template, name='delete_message_template'),
  

]