from django import template
from django.utils import timezone

register = template.Library()

@register.filter
def is_more_than_24_hours(lesson_time, now):
    if not lesson_time or not now:
        return False
    # Преобразуем now в datetime, если это строка или иное представление
    if isinstance(now, str):
        try:
            now = timezone.datetime.strptime(now, '%Y-%m-%d %H:%M:%S%z').replace(tzinfo=timezone.get_current_timezone())
        except (ValueError, TypeError):
            now = timezone.now()  # Фallback на текущее время с таймзоной
    time_threshold = lesson_time - timezone.timedelta(hours=24)
    print(f"Checking: lesson_time={lesson_time}, now={now}, threshold={time_threshold}")
    return now < time_threshold

@register.filter
def day_name(day_number):
    days = {
        0: 'Понедельник',
        1: 'Вторник',
        2: 'Среда',
        3: 'Четверг',
        4: 'Пятница',
        5: 'Суббота',
        6: 'Воскресенье',
    }
    return days.get(day_number, 'неизвестно')