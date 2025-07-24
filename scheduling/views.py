from django.views.generic import ListView, UpdateView, DeleteView
from django.views.generic.edit import FormMixin
from django.views.generic.base import View
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.http import HttpResponseNotFound, JsonResponse
from .models import Student, Teacher, Subject, TimeSlot, Lesson
from .forms import StudentForm, TeacherForm, SubjectForm, TimeSlotForm
from .optimization import calculate_schedule
from django.contrib import messages
from datetime import date

# Расчет расписания
class CalculateScheduleView(View):
    template_name = 'calculate_schedule.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        status = calculate_schedule()
        if status:
            return redirect('schedule')
        return render(request, 'error.html', {'message': 'Unable to calculate schedule.'})

# Просмотр расписания
class ScheduleView(ListView):
    model = Lesson
    template_name = 'schedule.html'
    context_object_name = 'schedule'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lessons = Lesson.objects.select_related('student', 'teacher', 'subject', 'time_slot').all()
        schedule = {i: [] for i in range(7)}
        for lesson in lessons:
            schedule[lesson.day_of_week].append(lesson)
        for day in schedule:
            schedule[day].sort(key=lambda x: x.time_slot.start_time)
        context['schedule'] = schedule
        return context

# Студенты: создание и список
class StudentListCreateView(ListView, FormMixin):
    model = Student
    form_class = StudentForm
    template_name = 'enter_students.html'
    context_object_name = 'students'

    def get_queryset(self):
        return Student.objects.select_related('teacher', 'subject').all()

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['form'] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            form.save()
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('students')

# Студенты: редактирование
class StudentUpdateView(UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'enter_students.html'
    success_url = reverse_lazy('students')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['students'] = Student.objects.select_related('teacher', 'subject').all()
        return context

    def get_object(self, queryset=None):
        try:
            return Student.objects.get(id=self.kwargs['pk'])
        except Student.DoesNotExist:
            return HttpResponseNotFound("<h2>Курсант не найден</h2>")

# Студенты: удаление
class StudentDeleteView(DeleteView):
    model = Student
    success_url = reverse_lazy('students')

    def get_object(self, queryset=None):
        try:
            return Student.objects.get(id=self.kwargs['pk'])
        except Student.DoesNotExist:
            return HttpResponseNotFound("<h2>Курсант не найден</h2>")

# Предметы: создание и список
class SubjectListCreateView(ListView, FormMixin):
    model = Subject
    form_class = SubjectForm
    template_name = 'enter_subjects.html'
    context_object_name = 'subjects'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['form'] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            form.save()
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('subjects')

# Предметы: редактирование
class SubjectUpdateView(UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'enter_subjects.html'
    success_url = reverse_lazy('subjects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subjects'] = Subject.objects.all()
        return context

    def get_object(self, queryset=None):
        try:
            return Subject.objects.get(id=self.kwargs['pk'])
        except Subject.DoesNotExist:
            return HttpResponseNotFound("<h2>Трансмиссия не найдена</h2>")

# Предметы: удаление
class SubjectDeleteView(DeleteView):
    model = Subject
    success_url = reverse_lazy('subjects')

    def get_object(self, queryset=None):
        try:
            return Subject.objects.get(id=self.kwargs['pk'])
        except Subject.DoesNotExist:
            return HttpResponseNotFound("<h2>Трансмиссия не найдена</h2>")

# Учителя: создание и список
class TeacherListCreateView(ListView, FormMixin):
    model = Teacher
    form_class = TeacherForm
    template_name = 'enter_teachers.html'
    context_object_name = 'teachers'

    def get_queryset(self):
        return Teacher.objects.select_related('subject').all()

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['form'] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            form.save()
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('teachers')

# Учителя: редактирование
class TeacherUpdateView(UpdateView):
    model = Teacher
    form_class = TeacherForm
    template_name = 'enter_teachers.html'
    success_url = reverse_lazy('teachers')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['teachers'] = Teacher.objects.select_related('subject').all()
        return context

    def get_object(self, queryset=None):
        try:
            return Teacher.objects.get(id=self.kwargs['pk'])
        except Teacher.DoesNotExist:
            return HttpResponseNotFound("<h2>Инструктор не найден</h2>")

# Учителя: удаление
class TeacherDeleteView(DeleteView):
    model = Teacher
    success_url = reverse_lazy('teachers')

    def get_object(self, queryset=None):
        try:
            return Teacher.objects.get(id=self.kwargs['pk'])
        except Teacher.DoesNotExist:
            return HttpResponseNotFound("<h2>Инструктор не найден</h2>")

# Временные отрезки: создание и список
class TimeSlotListCreateView(ListView, FormMixin):
    model = TimeSlot
    form_class = TimeSlotForm
    template_name = 'enter_time_slots.html'
    context_object_name = 'time_slots'

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['form'] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            form.save()
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('time_slots')

# Временные отрезки: редактирование
class TimeSlotUpdateView(UpdateView):
    model = TimeSlot
    form_class = TimeSlotForm
    template_name = 'enter_time_slots.html'
    success_url = reverse_lazy('time_slots')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['time_slots'] = TimeSlot.objects.all()
        return context

    def get_object(self, queryset=None):
        try:
            return TimeSlot.objects.get(id=self.kwargs['pk'])
        except TimeSlot.DoesNotExist:
            return HttpResponseNotFound("<h2>Временной отрезок не найден</h2>")

# Временные отрезки: удаление
class TimeSlotDeleteView(DeleteView):
    model = TimeSlot
    success_url = reverse_lazy('time_slots')

    def get_object(self, queryset=None):
        try:
            return TimeSlot.objects.get(id=self.kwargs['pk'])
        except TimeSlot.DoesNotExist:
            return HttpResponseNotFound("<h2>Временной отрезок не найден</h2>")

# Получение списка учителей для предмета
def get_teachers(request):
    subject_id = request.GET.get('subject_id')
    teachers = Teacher.objects.filter(subject_id=subject_id).select_related('subject').values('id', 'name')
    return JsonResponse(list(teachers), safe=False)


def mark_attendance(request):
    if request.method == 'POST':
        if 'save' in request.POST:
            # Обработка сохранения типа занятия
            for key, value in request.POST.items():
                if key.startswith('lesson_type_'):
                    lesson_id = key.split('_')[2]
                    lesson = Lesson.objects.get(id=lesson_id)
                    lesson.lesson_type = value
                    lesson.is_attended = value in ['autodrom', 'city']
                    lesson.save()
            messages.success(request, 'Типы занятий сохранены')

        elif 'confirm' in request.POST:
            # Обработка подтверждения посещений
            for key, value in request.POST.items():
                if key.startswith('lesson_type_'):
                    lesson_id = key.split('_')[2]
                    lesson = Lesson.objects.get(id=lesson_id)
                    if value in ['autodrom', 'city'] and lesson.is_attended:
                        student = lesson.student
                        if value == 'autodrom' and student.autodrom_hours > 0:
                            student.autodrom_hours -= 1
                        elif value == 'city' and student.city_hours > 0:
                            student.city_hours -= 1
                        student.save()
                        # Сбрасываем lesson_type и is_attended после зачёта
                        lesson.lesson_type = ''
                        lesson.is_attended = False
                        lesson.save()
            messages.success(request, 'Посещения засчитаны')

        return redirect('mark_attendance')

    # Получение расписания на текущую неделю
    # today = date.today()
    schedule = {}
    for day in range(7):
        lessons = Lesson.objects.filter(
            day_of_week=day
            # time_slot__start_time__gte=today
        ).order_by('time_slot__start_time')
        if lessons:
            schedule[day] = lessons

    return render(request, 'mark_attendance.html', {'schedule': schedule})