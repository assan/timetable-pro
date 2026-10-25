# booking/utils.py
from datetime import datetime, timedelta
from django.utils import timezone
from scheduling.models import Teacher, Student, TimeSlot, Lesson
from scheduling.optimization import parse_start_end, is_overlapping
from .models import Booking


DAYS_FIELDS = {
    0: 'monday_free_time',
    1: 'tuesday_free_time',
    2: 'wednesday_free_time',
    3: 'thursday_free_time',
    4: 'friday_free_time',
    5: 'saturday_free_time',
    6: 'sunday_free_time',
}


def get_free_slots(teacher, start_date=None, days_ahead=14, student=None):
    """
    Возвращает список свободных окон для инструктора.
    Каждое окно — dict с date, day_of_week, time_slot.
    Если передан student — дополнительно фильтрует по его свободному времени.
    """
    if start_date is None:
        start_date = timezone.now().date()

    time_slots = list(TimeSlot.objects.all().order_by('start_minutes'))
    free_slots = []

    for i in range(days_ahead):
        current_date = start_date + timedelta(days=i)
        day_of_week = current_date.weekday()
        field_name = DAYS_FIELDS[day_of_week]

        teacher_free = getattr(teacher, field_name, None)
        if not teacher_free or '-' not in teacher_free:
            continue

        try:
            t_start, t_end = parse_start_end(teacher_free)
        except Exception:
            continue

        # Уже занятые слоты этого инструктора на эту дату
        existing_lessons = Lesson.objects.filter(
            teacher=teacher,
            lesson_time__date=current_date,
            status__in=[0, 1, 2]  # не отменённые
        ).select_related('time_slot')

        existing_bookings = Booking.objects.filter(
            teacher=teacher,
            date=current_date,
            status__in=[0, 1]
        ).select_related('time_slot')

        busy_slots = [l.time_slot for l in existing_lessons] + [b.time_slot for b in existing_bookings]

        # Свободное время студента (если передан)
        s_start, s_end = None, None
        if student:
            student_free = getattr(student, field_name, None)
            if student_free and '-' in student_free:
                try:
                    s_start, s_end = parse_start_end(student_free)
                except Exception:
                    s_start = s_end = None

        for slot in time_slots:
            # Слот полностью внутри свободного времени инструктора
            if not (t_start <= slot.start_minutes and slot.end_minutes <= t_end):
                continue

            # Если есть студент — проверяем и его свободное время
            if student and s_start is not None:
                if not (s_start <= slot.start_minutes and slot.end_minutes <= s_end):
                    continue

            # Нет пересечений с уже занятыми слотами
            if any(is_overlapping(slot, busy) for busy in busy_slots):
                continue

            free_slots.append({
                'date': current_date,
                'day_of_week': day_of_week,
                'time_slot': slot,
                'teacher': teacher,
            })

    return free_slots