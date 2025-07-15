from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Obtener item de diccionario en template"""
    if isinstance(dictionary, dict) and key:
        return dictionary.get(str(key), [])
    return []

@register.filter
def stringformat(value, format_string):
    """Formatear string con formato específico"""
    try:
        if format_string == "02d":
            return f"{int(value):02d}"
        return format_string % value
    except (ValueError, TypeError):
        return str(value)

@register.filter
def add(value, arg):
    """Sumar valores o concatenar strings"""
    try:
        return str(value) + str(arg)
    except (ValueError, TypeError):
        return str(value)

@register.simple_tag
def format_date_key(year, month, day):
    """Formatear fecha para usar como clave"""
    try:
        year_int = int(year)
        month_int = int(month)
        day_int = int(day)
        return f"{year_int}-{month_int:02d}-{day_int:02d}"
    except (ValueError, TypeError):
        return ""

@register.filter
def subtract(value, arg):
    """Restar valores"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0