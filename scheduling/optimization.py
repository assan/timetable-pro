# templates/optimization.py
from scheduling.models import *
from datetime import time
from pulp import *
def parse_start_end(time):
    time=time.split('-')
    shm=time[0].split(':')
    ehm=time[1].split(':')
    return int(shm[0])*60+int(shm[1]), int(ehm[0])*60+int(ehm[1]),
def time_to_int(time):
    #time=time.split('-')
    hm=time.split(':')
    hour=int(hm[0])
    minute=int(hm[1])
    #minute=time[1].split(':')
    return hour*60+minute
def is_overlapping(time_slot1,time_slot2):
    st1=time_to_int(time_slot1.start_time)
    et1 = time_to_int(time_slot1.end_time)
    # st1, et1 = parse_start_end(time_slot1.time)
    st2 = time_to_int(time_slot2.start_time)
    et2 = time_to_int(time_slot2.end_time)
    return st2<st1<et2 or st2<et1<et2 or \
       st1 < st2 < et1 or st1 < et2 < et1
def init_time_slots():
    TimeSlot.objects.all().delete()
    #45 min
    for h in range(8,20):
        for m in range(0,46,15):
            start_time=str(h).zfill(2)+':'+str(m).zfill(2)
            end_h=(h*60+m+45)//60
            end_m=(h*60+m+45)%60
            end_time = str(end_h).zfill(2) + ':' + str(end_m).zfill(2)
            #time_slot=start_time+'-'+end_time
            TimeSlot.objects.create(start_time=start_time, end_time=end_time)
    # #90 min
    # for h in range(8,19):
    #     for m in range(0,46,15):
    #         start_time=str(h).zfill(2)+':'+str(m).zfill(2)
    #         end_h=(h*60+m+90)//60
    #         end_m=(h*60+m+90)%60
    #         end_time = str(end_h).zfill(2) + ':' + str(end_m).zfill(2)
    #         time_slot=start_time+'-'+end_time
    #         TimeSlot.objects.create(time=time_slot)
    # #120 min
    # for h in range(8,19):
    #     for m in range(0,46,15):
    #         start_time=str(h).zfill(2)+':'+str(m).zfill(2)
    #         end_h=(h*60+m+120)//60
    #         end_m=(h*60+m+120)%60
    #         end_time = str(end_h).zfill(2) + ':' + str(end_m).zfill(2)
    #         time_slot=start_time+'-'+end_time
    #         TimeSlot.objects.create(time=time_slot)
def init_availability():
    students = Student.objects.all()
    time_slots = TimeSlot.objects.all()
    Availability.objects.all().delete()
    teachers = Teacher.objects.all()
    subjects= Subject.objects.all()
    for day_of_week in range(7):
        for teacher in teachers:
            for student in students:
                for subject in subjects:
                    for time_slot in time_slots:
                        Availability.objects.create(student=student, time_slot=time_slot, teacher=teacher,\
                                                    day_of_week=day_of_week, subject=subject, available=False)
    days_of_week={0:'monday_free_time',
                  1:'tuesday_free_time',
                  2:"wednesday_free_time",
                  3:"thursday_free_time",
                  4:"friday_free_time",
                  5:"saturday_free_time",
                  6:"sunday_free_time"}
    for day in range(7):
        day_of_week = days_of_week[day]
        for student in students:
            if getattr(student, day_of_week):
                teacher=student.teacher
                for time_slot in time_slots:
                    free_time=getattr(student, day_of_week)
                    sft, eft = parse_start_end(free_time)
                    sts=time_to_int(time_slot.start_time)
                    ets=time_to_int(time_slot.end_time)
                    subject=student.subject
                    if sft<=sts and eft>=ets:
                        #print(student.name, time_slot.start_time, time_slot.end_time, teacher.name, day_of_week)
                        avail= Availability.objects.get(student=student, time_slot=time_slot, teacher=teacher, day_of_week=day, subject=subject)
                        avail.available= True
                        avail.save()



def calculate_schedule():
    init_time_slots()
    init_availability()
    students = Student.objects.all()
    teachers = Teacher.objects.all()
    subjects = Subject.objects.all()
    time_slots = TimeSlot.objects.all()
    availabilities = Availability.objects.all()

    # Создание модели
    model = LpProblem(name="templates", sense=LpMaximize)

    # Переменные: x[i][j][y][d][t] = 1 если урок y для студента i и учителя j назначен на день d в временной слот t, иначе 0
    x = LpVariable.dicts("x", [(i.id, j.id, y.id, d, t.id) for i in students for j in teachers for y in subjects for d in range(7) for t in time_slots], cat='Binary')


    # Ограничения
    # 1. Каждый учитель может проводить только один урок в одно и то же время
    T1 = LpVariable.dicts("T1", [(d, t.id, j.id) for d in range(7) for t in time_slots for j in teachers], 0, 1, LpInteger)
    for j in teachers:
        for d in range(7):
            for t in time_slots:
                model+=T1[d,t.id,j.id]==lpSum(x[i.id, j.id, y.id, d, t.id] for i in students for y in subjects)
                model+= T1[d,t.id,j.id] <= 1

    # 2. Каждый ученик может посещать только один урок в одно и то же время
    for i in students:
        for d in range(7):
            for t in time_slots:
                model += lpSum(x[i.id, j.id, y.id, d, t.id] for j in teachers for y in subjects) <= 1

    # 3. Каждый ученик может посещать не более одного урока по одному предмету в день
    for i in students:
        for y in subjects:
            for d in range(7):
                model += lpSum(x[i.id, j.id, y.id, d, t.id] for j in teachers for t in time_slots) <= 1

    # 4. Учесть доступность учеников
    for a in availabilities:
        if not a.available:
            model += lpSum(x[a.student.id, a.teacher.id, a.subject.id, a.day_of_week, a.time_slot.id]) == 0

    # # 5. Ограничение на количество аудиторий
    # for d in range(7):
    #     for t in time_slots:
    #         model += lpSum(x[i.id, j.id, y.id, d, t.id] for i in students for j in teachers for y in subjects) <= 5

    # 6. Ограничение на окна для учителя
    for j in teachers:
        for d in range(7):
            for t1 in time_slots:
                for t2 in time_slots:
                    if is_overlapping(t1, t2) and t1 != t2:
                        model += lpSum(x[i.id, j.id, y.id, d, t1.id] for i in students for y in subjects) +\
                                 lpSum(x[i.id, j.id, y.id, d, t2.id] for i in students for y in subjects) <= 1

    # 7. Ограничение на окна для ученика
    for i in students:
        for d in range(7):
            for t1 in time_slots:
                for t2 in time_slots:
                    if is_overlapping(t1, t2) and t1 != t2:
                        model += lpSum(x[i.id, j.id, y.id, d, t1.id] for j in teachers for y in subjects) +\
                                 lpSum(x[i.id, j.id, y.id, d, t2.id] for j in teachers for y in subjects) <= 1
    #8 Ограничение на желаемое количество занятий в неделю
    for i in students:
        model += lpSum(x[i.id, j.id, y.id,d, t.id] for d in range(7) for j in teachers for y in subjects for t in
                       time_slots) <= i.times_per_week



    # Целевая функция: максимизировать количество проведенных занятий
    model += lpSum( x[i.id, j.id, y.id, d, t.id] for i in students for j in teachers for y in subjects for d in range(7) for t in time_slots) #общее число занятий
             # -1/3*(lpSum(Surround1[d, u.id, y.id] for d in range(7) for u in time_slots for y in teachers))) #количество "окон" у учителей

    # Решение модели
    status = model.solve()

    # Создание расписания на основе решения модели
    if status:
        Lesson.objects.all().delete()  # Удаляем старые записи, чтобы обновить расписание
        for i in students:
            for j in teachers:
                for y in subjects:
                    for d in range(7):
                        for t in time_slots:
                            if x[i.id, j.id, y.id, d, t.id].value() == 1:
                                Lesson.objects.create(
                                    student=i,
                                    teacher=j,
                                    subject=y,
                                    day_of_week=d,
                                    time_slot=t
                                )
    return status
