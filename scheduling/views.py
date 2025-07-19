from django.shortcuts import render

# templates/views.py

from django.shortcuts import render, redirect
from .models import *
from .forms import *
from .optimization import calculate_schedule
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.http import JsonResponse
def get_teachers(request):
    subject_id = request.GET.get('subject_id')
    teachers = Teacher.objects.filter(subject_id=subject_id).values('id', 'name')
    return JsonResponse(list(teachers), safe=False)
def calculate_schedule_view(request):
    if request.method == 'POST':
        status = calculate_schedule()
        if status:
            return redirect('schedule')
        else:
            return render(request, 'error.html', {'message': 'Unable to calculate schedule.'})
    return render(request, 'calculate_schedule.html')

def schedule_view(request):
    # Получаем все уроки
    lessons = Lesson.objects.all()

    # Создаем словарь, где ключами будут дни недели, а значениями - соответствующие уроки
    schedule = {i: [] for i in range(7)}
    for lesson in lessons:
        schedule[lesson.day_of_week].append(lesson)

    # Сортируем уроки по времени начала внутри каждого дня
    for day in schedule:
        schedule[day].sort(key=lambda x: x.time_slot.start_time)

    context = {'schedule': schedule}
    return render(request, 'schedule.html', context)


def students_view(request):
    if request.method=='POST':
        form=StudentForm(request.POST)
        if form.is_valid():
            data=form.cleaned_data
            name=data.get('name')
            teacher = data.get('teacher')
            subject = data.get('subject')
            times_per_week=data.get('times_per_week')
            monday_free_time=data.get('monday_free_time')
            tuesday_free_time = data.get('tuesday_free_time')
            wednesday_free_time = data.get('wednesday_free_time')
            thursday_free_time = data.get('thursday_free_time')
            friday_free_time = data.get('friday_free_time')
            saturday_free_time = data.get('saturday_free_time')
            sunday_free_time = data.get('sunday_free_time')
            Student.objects.create(name=name, teacher=teacher, subject=subject, times_per_week=times_per_week, \
                                   monday_free_time= monday_free_time, tuesday_free_time=tuesday_free_time,  \
                                   wednesday_free_time = wednesday_free_time , thursday_free_time=thursday_free_time, \
                                   friday_free_time= friday_free_time,saturday_free_time=saturday_free_time, \
                                    sunday_free_time=sunday_free_time)
        students=Student.objects.all()
        return render(request,'enter_students.html',{'form':form,'students':students})

    form=StudentForm()
    students = Student.objects.all()
    return render(request, 'enter_students.html', {'form': form, 'students': students})


# изменение данных в бд
def edit_student(request, id):
    try:
        student = Student.objects.get(id=id)

        if request.method == "POST":
            form = StudentForm(request.POST, instance=student)
            if form.is_valid():
                form.save()
                return redirect("/students")
        else:
            form = StudentForm(instance=student)
            students = Student.objects.all()
            return render(request, "enter_students.html", {'form': form, 'students': students})
    except Student.DoesNotExist:
        return HttpResponseNotFound("<h2>Курсант не найден</h2>")


# удаление данных из бд
def delete_student(request, id):
    try:
        student = Student.objects.get(id=id)
        student.delete()
        return redirect("/students")
    except Student.DoesNotExist:
        return HttpResponseNotFound("<h2>Курсант не найден</h2>")
#==================================================================================
#Добавление, изменение и удаление предметов
def subject_view(request):
    if request.method=='POST':
        form=SubjectForm(request.POST)
        if form.is_valid():
            data=form.cleaned_data
            name=data.get('name')
            Subject.objects.create(name=name)
            subjects=Subject.objects.all()
        form=SubjectForm()
        return render(request,'enter_subjects.html',{'form':form,'subjects':subjects})
    form=SubjectForm()
    subjects = Subject.objects.all()
    return render(request, 'enter_subjects.html', {'form': form, 'subjects': subjects})


# изменение данных в бд
def edit_subject(request, id):
    try:
        subject = Subject.objects.get(id=id)

        if request.method == "POST":
            form=SubjectForm(request.POST)
            if form.is_valid():
                data=form.cleaned_data
                subject.name = data.get("name")
                subject.save()
            return redirect("/subjects")
        else:
            form = StudentForm()
            subjects = Subject.objects.all()
            return render(request, "enter_subjects.html",{'form':form,'subjects':subjects})
    except Subject.DoesNotExist:
        return HttpResponseNotFound("<h2>Трансмиссия не найдена</h2>")

# удаление данных из бд
def delete_subject(request, id):
    try:
        subject = Subject.objects.get(id=id)
        subject.delete()
        return redirect("/subjects")
    except Subject.DoesNotExist:
        return HttpResponseNotFound("<h2>Трансмиссия не найдена</h2>")
#==================================================================================
#Добавление, изменение и удаление инструкторов
def teacher_view(request):
    if request.method=='POST':
        form=TeacherForm(request.POST)
        if form.is_valid():
            data=form.cleaned_data
            name=data.get('name')
            subject=data.get('subject')
            Teacher.objects.create(name=name,subject=subject)
            teachers=Teacher.objects.all()
        form=TeacherForm()
        return render(request,'enter_teachers.html',{'form':form,'teachers':teachers})
    form=TeacherForm()
    teachers = Teacher.objects.all()
    return render(request, 'enter_teachers.html', {'form': form, 'teachers': teachers})


# изменение данных в бд
def edit_teacher(request, id):
    try:
        teacher = Teacher.objects.get(id=id)

        if request.method == "POST":
            form=TeacherForm(request.POST)
            if form.is_valid():
                data=form.cleaned_data
                teacher.name = data.get("name")
                teacher.subject=data.get('subject')
                teacher.save()
            return redirect("/teachers")
        else:
            form = TeacherForm()
            teachers = Teacher.objects.all()
            return render(request, "enter_teachers.html",{'form':form,'teachers':teachers})
    except Teacher.DoesNotExist:
        return HttpResponseNotFound("<h2>Инструктор не найден</h2>")

# удаление данных из бд
def delete_teacher(request, id):
    try:
       teacher = Teacher.objects.get(id=id)
       teacher.delete()
       return redirect("/teachers")
    except Teacher.DoesNotExist:
        return HttpResponseNotFound("<h2>Инструктор не найден</h2>")
#добавление временных отрезков (по умолчаению генерируются автоматически в optimization.py) Здесь только посмотреть на них
def time_slots_view(request):
    if request.method == 'POST':
        form = TimeSlotForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            time = data.get('time')
            TimeSlot.objects.create(time=time)
            time_slots = TimeSlot.objects.all()
        return render(request, 'enter_time_slots.html', {'form': form, 'time_slots': time_slots})
    form = TimeSlotForm()
    time_slots = TimeSlot.objects.all()
    return render(request, 'enter_time_slots.html', {'form': form, 'time_slots': time_slots})
def edit_time_slot(request, id):
    try:
        time_slot = TimeSlot.objects.get(id=id)
        if request.method == "POST":
            form=TimeSlotForm(request.POST)
            if form.is_valid():
                data=form.cleaned_data
                time_slot.time = data.get("time")
                time_slot.save()
            return redirect("/time_slots")
        else:
            form = TimeSlotForm()
            time_slots = TimeSlot.objects.all()
            return render(request, "enter_time_slots.html",{'form':form,'time_slots':time_slots})
    except TimeSlot.DoesNotExist:
        return HttpResponseNotFound("<h2>Временной отрезок не найден</h2>")

# удаление данных из бд
def delete_time_slot(request, id):
    try:
        time_slot = TimeSlot.objects.get(id=id)
        time_slot.delete()
        return redirect("/time_slots")
    except Student.DoesNotExist:
        return HttpResponseNotFound("<h2>Временной отрезок не найден</h2>")