# blog/templatetags/my_filters.py

from django import template
import re

register = template.Library()

@register.filter
def remove_special_chars(value):
    return re.sub('[^a-zA-Z]', '', value)