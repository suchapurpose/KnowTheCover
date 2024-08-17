from django import template
import json

register = template.Library()

@register.filter
def pretty_json(value):
    return json.dumps(value, indent=4, ensure_ascii=False)

@register.filter
def is_dict(value):
    return isinstance(value, dict)

@register.filter
def is_list(value):
    return isinstance(value, list)