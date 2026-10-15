# booking/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from django.views.decorators.http import require_POST

from scheduling.models import Teacher, Student, Subject, Lesson, TimeSlot
from autorization.views import is_admin, is_student
from .models import Booking
from .utils import get_free_slots


@login_required
def free_slots_view(request):
    """Список свободных окон + форма бронирования"""
    context = {}
    teachers = Teacher.objects.all().select_related('subject')
    selected_teacher = None
    selected_student = None

    # Для студента — автоматически его профиль и его инструктор (если есть)
    if request.user.userprofile.role == 'student':
        try:
            selected_student = Student.objects.get(user=request.user)
            selected_teacher = selected_student.teacher
        except Student.DoesNotExist:
            messages.error(request, 'Профиль курсанта не найден.')
            return redirect('autorization:student_dashboard')

    # Админ может выбирать
    teacher_id = request.GET.get('teacher')
    if teacher_id and (request.user.userprofile.role == 'admin' or not selected_teacher):
        selected_teacher = get_object_or_404(Teacher, id=teacher_id)

    free_slots = []
    if selected_teacher:
        free_slots = get_free_slots(
            teacher=selected_teacher,
            days_ahead=14,
            student=selected_student
        )

    context.update({
        'teachers': teachers,
        'selected_teacher': selected_teacher,
        'selected_student': selected_student,
        'free_slots': free_slots,
        'is_admin': request.user.userprofile.role == 'admin',
    })
    return render(request, 'booking/free_slots.html', context)


@login_required
@require_POST
def book_slot(request):
    """Создание брони"""
    teacher_id = request.POST.get('teacher_id')
    time_slot_id = request.POST.get('time_slot_id')
    date_str = request.POST.get('date')
    student_id = request.POST.get('student_id')

    teacher = get_object_or_404(Teacher, id=teacher_id)
    time_slot = get_object_or_404(TimeSlot, id=time_slot_id)
    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    day_of_week = date.weekday()

    # Определяем студента
    if request.user.userprofile.role == 'student':
        student = get_object_or_404(Student, user=request.user)
    else:
        # Админ обязан указать студента
        if not student_id:
            messages.error(request, 'Выберите курсанта.')
            return redirect('booking:free_slots')
        student = get_object_or_404(Student, id=student_id)

    # Проверка, что слот всё ещё свободен
    existing = Booking.objects.filter(
        teacher=teacher, date=date, time_slot=time_slot, status__in=[0, 1]
    ).exists()
    lesson_exists = Lesson.objects.filter(
        teacher=teacher,
        lesson_time__date=date,
        time_slot=time_slot,
        status__in=[0, 1, 2]
    ).exists()

    if existing or lesson_exists:
        messages.error(request, 'Это окно уже занято.')
        return redirect(request.META.get('HTTP_REFERER', 'booking:free_slots'))

    # Создаём бронь
    booking = Booking.objects.create(
        student=student,
        teacher=teacher,
        subject=student.subject or teacher.subject,
        time_slot=time_slot,
        date=date,
        day_of_week=day_of_week,
        status=1,  # сразу подтверждаем (можно поставить 0, если нужно подтверждение)
    )

    # Создаём урок
    lesson_time = timezone.make_aware(
        datetime.combine(date, datetime.min.time()).replace(
            hour=time_slot.start_minutes // 60,
            minute=time_slot.start_minutes % 60
        )
    )

    lesson = Lesson.objects.create(
        student=student,
        teacher=teacher,
        subject=booking.subject,
        day_of_week=day_of_week,
        time_slot=time_slot,
        lesson_time=lesson_time,
        status=1,  # Подтверждено
    )

    booking.lesson = lesson
    booking.save()

    messages.success(request, f'Занятие успешно забронировано: {date} {time_slot}')
    return redirect('booking:free_slots')