from django import template
from django.utils import timezone
import datetime

register = template.Library()

@register.filter
def add_days(date_str, days):
    date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    return date + datetime.timedelta(days=int(days))