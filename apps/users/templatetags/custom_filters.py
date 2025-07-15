from django import template
import json

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """
    Busca una clave en un diccionario o string JSON
    """
    if isinstance(dictionary, str):
        try:
            dictionary = json.loads(dictionary)
        except (json.JSONDecodeError, TypeError):
            return ''
    
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''

@register.filter
def replace(value, args):
    """
    Reemplaza ocurrencias de una cadena por otra
    Uso: {{ "hola_mundo"|replace:"_,  " }}
    """
    if ',' in args:
        search, replace_with = args.split(',', 1)
        return value.replace(search, replace_with)
    return value
