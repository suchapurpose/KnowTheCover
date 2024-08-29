from django import template
import json

register = template.Library()

# Pretty print JSON in templates
@register.filter
def pretty_json(value):
    return json.dumps(value, indent=4, ensure_ascii=False)

# Check if a value is a dictionary
@register.filter
def is_dict(value):
    return isinstance(value, dict)

# Check if a value is a list
@register.filter
def is_list(value):
    return isinstance(value, list)