from scheduling.models import *
from datetime import time, datetime, timedelta
from pulp import *
from django.utils import timezone
import logging

def parse_start_end(time):
    time = time.split('-')
    shm = time[0].split(':')
    ehm = time[1].split(':')
    return int(shm[0]) * 60 + int(shm[1]), int(ehm[0]) * 60 + int(ehm[1])

def time_to_int(time):
    hm = time.split(':')
    return int(hm[0]) * 60 + int(hm[1])

def is_overlapping(time_slot1, time_slot2):
    st1, et1 = time_slot1.start_minutes, time_slot1.end_minutes
    st2, et2 = time_slot2.start_minutes, time_slot2.end_minutes
    return max(st1,st2)<min(et1,et2)

def init_time_slots():
    TimeSlot.objects.all().delete()
    time_slots = []
    for h in range(8, 20):
        for m in range(0, 46, 15):
            start_time = f"{h:02d}:{m:00}"
            end_h = (h * 60 + m + 90) // 60
            end_m = (h * 60 + m + 90) % 60
            end_time = f"{end_h:02d}:{end_m:00}"
            time_slots.append(
                TimeSlot(
                    start_time=start_time,
                    end_time=end_time,
                    start_minutes=h * 60 + m,
                    end_minutes=end_h * 60 + end_m
                )
            )
    TimeSlot.objects.bulk_create(time_slots)

def init_availability():
    Availability.objects.all().delete()
    students = Student.objects.select_related('teacher', 'subject').all()
    time_slots = TimeSlot.objects.all()
    days_of_week = {
        0: 'monday_free_time', 1: 'tuesday_free_time', 2: 'wednesday_free_time',
        3: 'thursday_free_time', 4: 'friday_free_time', 5: 'saturday_free_time',
        6: 'sunday_free_time'
    }
    availabilities = []
    logging.info("Working")
    for day in range(7):
        day_of_week = days_of_week[day]
        for student in students:
            logging.debug(student)
            if getattr(student, day_of_week):  # Проверяем, что у студента есть свободное время
                teacher = student.teacher
                if teacher is None:  # Пропускаем студентов без инструктора
                    continue
                subject = student.subject
                student_free_time = getattr(student, day_of_week)
                sfts, efts = parse_start_end(student_free_time)
                teacher_free_time = getattr(teacher, day_of_week)
                if not teacher_free_time:  # Пропускаем, если у инструктора нет свободного времени
                    continue
                sftt, eftt = parse_start_end(teacher_free_time)
                for time_slot in time_slots:
                    if sfts <= time_slot.start_minutes and efts >= time_slot.end_minutes \
                            and sftt <= time_slot.start_minutes and eftt >= time_slot.end_minutes:
                        print(student, time_slot)
                        availabilities.append(
                            Availability(
                                student=student,
                                time_slot=time_slot,
                                teacher=teacher,
                                day_of_week=day,
                                subject=subject,
                                available=True
                            )
                        )
    Availability.objects.bulk_create(availabilities)

def calculate_schedule():
    init_time_slots()
    init_availability()
    students = Student.objects.select_related('teacher', 'subject').all()
    teachers = Teacher.objects.all()
    subjects = Subject.objects.all()
    time_slots = TimeSlot.objects.all()
    availabilities = Availability.objects.select_related('student', 'teacher', 'subject', 'time_slot').all()
    # Создание модели
    model = LpProblem(name="templates", sense=LpMaximize)
    # Переменные только для доступных комбинаций
    x = LpVariable.dicts(
        "x",
        [(a.student.id, a.teacher.id, a.subject.id, a.day_of_week, a.time_slot.id)
         for a in availabilities if a.available],
        cat='Binary'
    )

    # Ограничения
    # 1. Каждый учитель может проводить только один урок в одно и то же время
    T1 = LpVariable.dicts("T1", [(d, t.id, j.id) for d in range(7) for t in time_slots for j in teachers], 0, 1, LpInteger)
    for j in teachers:
        for d in range(7):
            for t in time_slots:
                model += T1[d, t.id, j.id] == lpSum(x.get((i.id, j.id, y.id, d, t.id), 0) for i in students for y in subjects)
                model += T1[d, t.id, j.id] <= 1
    # 2. Каждый ученик может посещать только один урок в одно и то же время
    for i in students:
        for d in range(7):
            for t in time_slots:
                model += lpSum(x.get((i.id, j.id, y.id, d, t.id), 0) for j in teachers for y in subjects) <= 1
    # 3. Каждый ученик может посещать не более одного урока по одному предмету в день
    for i in students:
        for y in subjects:
            for d in range(7):
                model += lpSum(x.get((i.id, j.id, y.id, d, t.id), 0) for j in teachers for t in time_slots) <= 1

    # Предварительно вычисленные пересечения
    overlapping_pairs = [(t1, t2) for t1 in time_slots for t2 in time_slots if t1 != t2 and is_overlapping(t1, t2)]
    # 4. Только одно занятие в пересекающихся отрезках времени для каждого учителя
    for j in teachers:
        for d in range(7):
            for t1, t2 in overlapping_pairs:
                model += lpSum(x.get((i.id, j.id, y.id, d, t1.id), 0) for i in students for y in subjects) + \
                         lpSum(x.get((i.id, j.id, y.id, d, t2.id), 0) for i in students for y in subjects) <= 1
    # 5. Только одно занятие в пересекающихся отрезках времени для каждого ученика
    for i in students:
        for d in range(7):
            for t1, t2 in overlapping_pairs:
                model += lpSum(x.get((i.id, j.id, y.id, d, t1.id), 0) for j in teachers for y in subjects) + \
                         lpSum(x.get((i.id, j.id, y.id, d, t2.id), 0) for j in teachers for y in subjects) <= 1
    # 6. Ограничение спроса - количество занятий в неделю для каждого ученика
    for i in students:
        model += lpSum(x.get((i.id, j.id, y.id, d, t.id), 0) for d in range(7) for j in teachers for y in subjects for t in time_slots) <= i.times_per_week
    # Построение целевой функции - сумма количества проведённых уроков
    model += lpSum(x.values())
    # Решение модели
    status = model.solve()
    # Выгрузка рассчитанного расписания в модель Lessons с lesson_time
    if status:
        Lesson.objects.all().delete()
        today = timezone.now().date()
        current_weekday = today.weekday()  # 0 = понедельник, 6 = воскресенье
        for a in availabilities:
            if a.available and x.get((a.student.id, a.teacher.id, a.subject.id, a.day_of_week, a.time_slot.id), 0).value() == 1:
                # Вычисляем lesson_time для следующей недели
                current_weekday = today.weekday()  # 0 = понедельник, 1 = вторник и т.д.
                days_to_add = (a.day_of_week - current_weekday + 7)
                lesson_date = today + timedelta(days=days_to_add)
                # Извлекаем start_time из time_slot.start_time (например, "08:00" из "08:00-08:45")
                start_time_str = a.time_slot.start_time.split('-')[0]  # Берем только начальное время
                hour, minute = map(int, start_time_str.split(':'))
                lesson_time = timezone.make_aware(
                    datetime.combine(lesson_date, datetime.min.time()).replace(hour=hour, minute=minute))
                # Создаём занятие
                Lesson.objects.create(
                    student=a.student,
                    teacher=a.teacher,
                    subject=a.subject,
                    day_of_week=a.day_of_week,
                    time_slot=a.time_slot,
                    lesson_time=lesson_time,
                    status=0  # scheduled по умолчанию
                )
    return status