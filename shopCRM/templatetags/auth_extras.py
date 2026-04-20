# shopCRM/templatetags/auth_extras.py
from django import template
from shopCRM.views import get_user_level # Імпортуємо вашу функцію

register = template.Library()

@register.filter(name='user_level')
def user_level(user):
    return get_user_level(user)