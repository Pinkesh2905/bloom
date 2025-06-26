from django import template

register = template.Library()

@register.filter
def lookup(dict_obj, key):
    return dict_obj.get(key.lower())  # ensure it's lowercase if needed
