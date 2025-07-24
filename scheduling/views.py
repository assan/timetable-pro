from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
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
from autorization.views import is_admin  # Импортируем проверку роли

# Декораторы для защиты представлений
decorators = [login_required, user_passes_test(is_admin)]

# Студенты: создание и список
@method_decorator(decorators, name='dispatch')
class StudentListCreateView(ListView, FormMixin):
    model = Student
    form_class = StudentForm
    template_name = 'scheduling/enter_students.html'
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
        return reverse_lazy('scheduling:students')

# Студенты: редактирование
@method_decorator(decorators, name='dispatch')
class StudentUpdateView(UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'scheduling/enter_students.html'
    success_url = reverse_lazy('scheduling:students')

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
@method_decorator(decorators, name='dispatch')
class StudentDeleteView(DeleteView):
    model = Student
    success_url = reverse_lazy('scheduling:students')

    def get_object(self, queryset=None):
        try:
            return Student.objects.get(id=self.kwargs['pk'])
        except Student.DoesNotExist:
            return HttpResponseNotFound("<h2>Курсант не найден</h2>")

# Предметы: создание и список
@method_decorator(decorators, name='dispatch')
class SubjectListCreateView(ListView, FormMixin):
    model = Subject
    form_class = SubjectForm
    template_name = 'scheduling/enter_subjects.html'
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
        return reverse_lazy('scheduling:subjects')

# Предметы: редактирование
@method_decorator(decorators, name='dispatch')
class SubjectUpdateView(UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'scheduling/enter_subjects.html'
    success_url = reverse_lazy('scheduling:subjects')

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
@method_decorator(decorators, name='dispatch')
class SubjectDeleteView(DeleteView):
    model = Subject
    success_url = reverse_lazy('scheduling:subjects')

    def get_object(self, queryset=None):
        try:
            return Subject.objects.get(id=self.kwargs['pk'])
        except Subject.DoesNotExist:
            return HttpResponseNotFound("<h2>Трансмиссия не найдена</h2>")

# Учителя: создание и список
@method_decorator(decorators, name='dispatch')
class TeacherListCreateView(ListView, FormMixin):
    model = Teacher
    form_class = TeacherForm
    template_name = 'scheduling/enter_teachers.html'
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
        return reverse_lazy('scheduling:teachers')

# Учителя: редактирование
@method_decorator(decorators, name='dispatch')
class TeacherUpdateView(UpdateView):
    model = Teacher
    form_class = TeacherForm
    template_name = 'scheduling/enter_teachers.html'
    success_url = reverse_lazy('scheduling:teachers')

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
@method_decorator(decorators, name='dispatch')
class TeacherDeleteView(DeleteView):
    model = Teacher
    success_url = reverse_lazy('scheduling:teachers')

    def get_object(self, queryset=None):
        try:
            return Teacher.objects.get(id=self.kwargs['pk'])
        except Teacher.DoesNotExist:
            return HttpResponseNotFound("<h2>Инструктор не найден</h2>")

# Временные отрезки: создание и список
@method_decorator(decorators, name='dispatch')
class TimeSlotListCreateView(ListView, FormMixin):
    model = TimeSlot
    form_class = TimeSlotForm
    template_name = 'scheduling/enter_time_slots.html'
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
        return reverse_lazy('scheduling:time_slots')

# Временные отрезки: редактирование
@method_decorator(decorators, name='dispatch')
class TimeSlotUpdateView(UpdateView):
    model = TimeSlot
    form_class = TimeSlotForm
    template_name = 'scheduling/enter_time_slots.html'
    success_url = reverse_lazy('scheduling:time_slots')

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
@method_decorator(decorators, name='dispatch')
class TimeSlotDeleteView(DeleteView):
    model = TimeSlot
    success_url = reverse_lazy('scheduling:time_slots')

    def get_object(self, queryset=None):
        try:
            return TimeSlot.objects.get(id=self.kwargs['pk'])
        except TimeSlot.DoesNotExist:
            return HttpResponseNotFound("<h2>Временной отрезок не найден</h2>")

# Расчет расписания
@method_decorator(decorators, name='dispatch')
class CalculateScheduleView(View):
    template_name = 'scheduling/calculate_schedule.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        status = calculate_schedule()
        if status:
            return redirect('scheduling:schedule')
        return render(request, 'scheduling/error.html', {'message': 'Unable to calculate schedule.'})

# Просмотр расписания
class ScheduleView(ListView):
    model = Lesson
    template_name = 'scheduling/schedule.html'
    context_object_name = 'schedule'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        lessons = Lesson.objects.select_related('student', 'teacher', 'subject', 'time_slot').all()
        schedule = {i: [] for i in range(7)}
        for lesson in lessons:
            schedule[lesson.day_of_week].append(lesson)
        for day in schedule:
            schedule[day].sort(key=lambda x: x.time_slot.start_time)
        context['schedule'] = schedule
        return context

# Получение списка учителей для предмета
@login_required
@user_passes_test(is_admin)
def get_teachers(request):
    subject_id = request.GET.get('subject_id')
    teachers = Teacher.objects.filter(subject_id=subject_id).select_related('subject').values('id', 'name')
    return JsonResponse(list(teachers), safe=False)

# Отметка посещаемости
@login_required
def mark_attendance(request):
    if request.method == 'POST':
        if 'confirm' in request.POST:
            for key, value in list(request.POST.items()):
                if key.startswith('lesson_type_'):
                    lesson_id = key.split('_')[2]
                    lesson = Lesson.objects.get(id=lesson_id)
                    lesson.lesson_type = value
                    lesson.is_attended = value in ['autodrom', 'city']
                    if lesson.is_attended:
                        student = lesson.student
                        if value == 'autodrom' and student.autodrom_hours > 0:
                            student.autodrom_hours -= 1
                        elif value == 'city' and student.city_hours > 0:
                            student.city_hours -= 1
                        student.save()
                        lesson.lesson_type = ''
                        lesson.is_attended = False
                    lesson.save()
            messages.success(request, 'Посещения засчитаны')
        return redirect('scheduling:attendance')

    schedule = {}
    for day in range(7):
        lessons = Lesson.objects.filter(day_of_week=day).order_by('time_slot__start_time')
        if lessons:
            schedule[day] = lessons

    return render(request, 'scheduling/mark_attendance.html', {'schedule': schedule})