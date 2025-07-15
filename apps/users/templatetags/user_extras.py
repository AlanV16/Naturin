from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a key"""
    if hasattr(dictionary, 'get'):
        return dictionary.get(key, [])
    return []

@register.filter
def pluralize_es(value, arg=""):
    """Spanish pluralization filter"""
    try:
        count = int(value)
        if count == 1:
            return ""
        else:
            return arg if arg else "s"
    except (ValueError, TypeError):
        return arg if arg else "s"

@register.filter
def is_online(user):
    """
    Determina si un usuario está 'conectado' basándose en su último acceso
    Se considera conectado si se logueó en los últimos 5 minutos
    """
    if not user.last_login:
        return False
    
    # Considera conectado si se logueó en los últimos 5 minutos
    five_minutes_ago = timezone.now() - timedelta(minutes=5)
    return user.last_login >= five_minutes_ago

@register.filter
def connection_status(user):
    """
    Retorna el estado de conexión como texto
    """
    if is_online(user):
        return "Conectado"
    elif user.last_login:
        return "Desconectado"
    else:
        return "Nunca conectado"

@register.filter
def connection_status_class(user):
    """
    Retorna las clases CSS para el estado de conexión
    """
    if is_online(user):
        return "bg-green-100 text-green-800"
    elif user.last_login:
        return "bg-yellow-100 text-yellow-800"
    else:
        return "bg-gray-100 text-gray-800"
