from django import template

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
