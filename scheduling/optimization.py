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

def calculate_schedule(premium=False, stability_weight=8.0, satisfaction_weight=3.0):
    init_time_slots()
    init_availability()

    students = list(Student.objects.select_related('teacher', 'subject').all())
    teachers = list(Teacher.objects.all())
    subjects = list(Subject.objects.all())
    time_slots = list(TimeSlot.objects.all())
    availabilities = list(
        Availability.objects.select_related('student', 'teacher', 'subject', 'time_slot')
        .filter(available=True)
    )

    # ---------- Предыдущее расписание (для стабилизации) ----------
    previous = set()
    if premium:
        for lesson in Lesson.objects.filter(status__in=[0, 1]).select_related(
            'student', 'teacher', 'subject', 'time_slot'
        ):
            key = (
                lesson.student_id,
                lesson.teacher_id,
                lesson.subject_id,
                lesson.day_of_week,
                lesson.time_slot_id,
            )
            previous.add(key)

    # ---------- Создание модели ----------
    model = LpProblem(name="timetable", sense=LpMaximize)

    # Переменные только для доступных комбинаций
    x = LpVariable.dicts(
        "x",
        [
            (a.student.id, a.teacher.id, a.subject.id, a.day_of_week, a.time_slot.id)
            for a in availabilities
        ],
        cat="Binary",
    )

    # ---------- Жёсткие ограничения (как у вас сейчас) ----------
    # 1. Учитель — не более одного занятия в слот
    T1 = LpVariable.dicts(
        "T1",
        [(d, t.id, j.id) for d in range(7) for t in time_slots for j in teachers],
        0, 1, LpInteger,
    )
    for j in teachers:
        for d in range(7):
            for t in time_slots:
                model += T1[d, t.id, j.id] == lpSum(
                    x.get((i.id, j.id, y.id, d, t.id), 0)
                    for i in students for y in subjects
                )
                model += T1[d, t.id, j.id] <= 1

    # 2. Студент — не более одного занятия в слот
    for i in students:
        for d in range(7):
            for t in time_slots:
                model += lpSum(
                    x.get((i.id, j.id, y.id, d, t.id), 0)
                    for j in teachers for y in subjects
                ) <= 1

    # 3. Не более одного занятия по предмету в день у студента
    for i in students:
        for y in subjects:
            for d in range(7):
                model += lpSum(
                    x.get((i.id, j.id, y.id, d, t.id), 0)
                    for j in teachers for t in time_slots
                ) <= 1

    # 4–5. Пересечения слотов (учитель и студент)
    overlapping_pairs = [
        (t1, t2) for t1 in time_slots for t2 in time_slots
        if t1 != t2 and is_overlapping(t1, t2)
    ]
    for j in teachers:
        for d in range(7):
            for t1, t2 in overlapping_pairs:
                model += (
                    lpSum(x.get((i.id, j.id, y.id, d, t1.id), 0) for i in students for y in subjects)
                    + lpSum(x.get((i.id, j.id, y.id, d, t2.id), 0) for i in students for y in subjects)
                ) <= 1

    for i in students:
        for d in range(7):
            for t1, t2 in overlapping_pairs:
                model += (
                    lpSum(x.get((i.id, j.id, y.id, d, t1.id), 0) for j in teachers for y in subjects)
                    + lpSum(x.get((i.id, j.id, y.id, d, t2.id), 0) for j in teachers for y in subjects)
                ) <= 1

    # 6. Лимит занятий в неделю
    for i in students:
        model += lpSum(
            x.get((i.id, j.id, y.id, d, t.id), 0)
            for d in range(7) for j in teachers for y in subjects for t in time_slots
        ) <= i.times_per_week

    # ---------- Мягкие ограничения / целевая функция (premium) ----------
    # Базовая часть — максимизация количества занятий
    obj = lpSum(x.values())

    if premium:
        # 1. Стабилизация: бонус за совпадение с предыдущей неделей
        for key in previous:
            if key in x:
                obj += stability_weight * x[key]

        # 2. Удовлетворённость: бонус, если назначено ≥ половины запрошенного
        satisfied = LpVariable.dicts(
            "satisfied",
            [i.id for i in students],
            cat="Binary",
        )

        for i in students:
            half = max(1, i.times_per_week // 2)  # порог «половина запрошенных»
            total = lpSum(
                x.get((i.id, j.id, y.id, d, t.id), 0)
                for d in range(7) for j in teachers for y in subjects for t in time_slots
            )
            # Если total >= half, можно поставить satisfied = 1
            model += total >= half * satisfied[i.id]

        obj += satisfaction_weight * lpSum(satisfied.values())

    model += obj

    # ---------- Решение ----------
    status = model.solve(PULP_CBC_CMD(msg=False, timeLimit=30, gapRel=0.05))

    # Дальше ваша существующая логика сохранения Lesson
    # (можно оставить почти без изменений)
    if LpStatus[status] in ("Optimal", "Feasible"):
        Lesson.objects.all().delete()
        # ... ваш код создания Lesson по x.value() == 1 ...
        # Рекомендуется также сохранить метрики:
        # - сколько слотов совпало с previous
        # - сколько студентов удовлетворено (satisfied[i.id].value() == 1)

    return status