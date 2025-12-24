
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Pobiera wartość ze słownika dla danego klucza"""
    return dictionary.get(key)