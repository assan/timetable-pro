from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import ListView, UpdateView, DeleteView
from django.views.generic.edit import FormMixin
from django.views.generic.base import View
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect
from django.http import HttpResponseNotFound, JsonResponse, HttpResponseRedirect
from .models import Student, Teacher, Subject, TimeSlot, Lesson
from .forms import StudentForm, TeacherForm, SubjectForm, TimeSlotForm
from .optimization import calculate_schedule
from django.contrib import messages
from autorization.views import is_admin  # Импортируем проверку роли
from autorization.forms import StudentProfileForm
from django.utils import timezone

# Декораторы для защиты представлений
decorators = [login_required, user_passes_test(is_admin)]
# Расчет расписания
@method_decorator(decorators, name='dispatch')
class CalculateScheduleView(View):
    template_name = 'scheduling/calculate_schedule.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        status = calculate_schedule()
        if status:
            messages.success(request, 'Расписание успешно рассчитано!')
            return redirect('scheduling:schedule')
        messages.error(request, 'Не удалось рассчитать расписание.')
        return render(request, 'scheduling/error.html', {'message': 'Unable to calculate schedule.'})

# Просмотр расписания
@method_decorator(decorators, name='dispatch')
class ScheduleView(ListView):
    model = Lesson
    template_name = 'scheduling/schedule.html'
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
        context['timezone'] = timezone  # Убедитесь, что timezone доступен
        return context

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
@method_decorator([login_required, user_passes_test(is_admin)], name='dispatch')
class StudentDeleteView(DeleteView):
    model = Student
    success_url = reverse_lazy('scheduling:students')
    template_name = 'scheduling/student_confirm_delete.html'

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


# Получение списка учителей для предмета
@login_required
@user_passes_test(is_admin)
def get_teachers(request):
    subject_id = request.GET.get('subject_id')
    teachers = Teacher.objects.filter(subject_id=subject_id).select_related('subject').values('id', 'name')
    return JsonResponse(list(teachers), safe=False)

# Отметка посещаемости
@login_required
@user_passes_test(is_admin)
def mark_attendance(request):
    if request.method == 'POST':
        if 'confirm' in request.POST:
            for key, value in list(request.POST.items()):
                if key.startswith('lesson_type_'):
                    lesson_id = key.split('_')[2]
                    try:
                        lesson = Lesson.objects.get(id=lesson_id, status=1)  # Только подтверждённые занятия
                        if value not in ['autodrom', 'city']:
                            messages.error(request, f'Ошибка: Неверный тип занятия для урока {lesson_id}.')
                            continue

                        lesson.lesson_type = value
                        lesson.status = 2  # Отметка как проведённое
                        lesson.save()

                        # Уменьшение часов ученика
                        student = lesson.student
                        time_slot = lesson.time_slot
                        duration_hours = (time_slot.end_minutes - time_slot.start_minutes) / 60.0  # Длительность в часах

                        if duration_hours <= 0:
                            messages.error(request, f'Ошибка: Неверная длительность занятия для {lesson.student}.')
                            continue

                        if value == 'autodrom':
                            student.autodrom_hours = max((student.autodrom_hours or 0) - duration_hours, 0)
                        elif value == 'city':
                            student.city_hours = max((student.city_hours or 0) - duration_hours, 0)
                        student.save()

                        messages.success(request,
                                         f'Занятие с {lesson.student} отмечено как проведённое ({lesson.get_lesson_type_display()}).')
                    except Lesson.DoesNotExist:
                        messages.error(request, f'Ошибка: Занятие {lesson_id} не найдено или не может быть отмечено.')
            messages.success(request, 'Посещения засчитаны')
        return redirect('scheduling:mark_attendance')

    schedule = {}
    for day in range(7):
        lessons = Lesson.objects.filter(day_of_week=day).order_by('time_slot__start_time')
        if lessons:
            schedule[day] = lessons

    return render(request, 'scheduling/mark_attendance.html', {'schedule': schedule})
@login_required
def confirm_lessons(request):
    if request.method == 'POST':
        student = request.user.student if hasattr(request.user, 'student') else None
        is_admin_user = is_admin(request.user)

        scroll_position = request.POST.get('scroll_position')
        lesson_id = None
        for key in request.POST:
            if key.startswith('confirm_') or key.startswith('cancel_'):
                lesson_id = key.replace('confirm_', '').replace('cancel_', '')

        for key, value in request.POST.items():
            if key.startswith('confirm_'):
                lesson_id = key.replace('confirm_', '')
                try:
                    if student and not is_admin_user:
                        lesson = Lesson.objects.get(id=lesson_id, student=student)
                    else:
                        lesson = Lesson.objects.get(id=lesson_id)
                    if lesson.status == 0 and int(value) == 1:
                        lesson.status = 1
                        lesson.save()
                        print(f"Confirmed lesson {lesson_id}")
                        messages.success(request, f'Занятие {lesson_id} подтверждено.')
                    else:
                        messages.error(request, f'Невозможно подтвердить занятие {lesson_id} (не в статусе scheduled).')
                except Lesson.DoesNotExist:
                    messages.error(request, f'Занятие {lesson_id} не найдено или недоступно.')
            elif key.startswith('cancel_'):
                lesson_id = key.replace('cancel_', '')
                try:
                    if student and not is_admin_user:
                        lesson = Lesson.objects.get(id=lesson_id, student=student)
                    else:
                        lesson = Lesson.objects.get(id=lesson_id)
                    current_time = timezone.now()
                    time_threshold = lesson.lesson_time - timezone.timedelta(hours=24)
                    print(f"Debug: lesson_id={lesson_id}, lesson_time={lesson.lesson_time}, now={current_time}, threshold={time_threshold}")
                    if lesson.status == 1 and current_time < time_threshold:
                        lesson.status = 3
                        lesson.save()
                        messages.success(request, f'Занятие {lesson_id} отменено.')
                    else:
                        messages.error(request, f'Отмена занятия {lesson_id} невозможна (менее 24 часов или не в статусе confirmed).')
                except Lesson.DoesNotExist:
                    messages.error(request, f'Занятие {lesson_id} не найдено или недоступно.')
            elif key == 'save':
                pass

        if student and not is_admin_user:
            form = StudentProfileForm(instance=student)
            lessons = Lesson.objects.filter(student=student).order_by('lesson_time')
            return render(request, 'autorization/student_dashboard.html', {
                'form': form,
                'student': student,
                'lessons': lessons,
                'now': timezone.now()
            })
        else:
            lessons = Lesson.objects.select_related('student', 'teacher', 'subject', 'time_slot').all()
            schedule = {i: [] for i in range(7)}
            for lesson in lessons:
                schedule[lesson.day_of_week].append(lesson)
            for day in schedule:
                schedule[day].sort(key=lambda x: x.time_slot.start_time)
            if scroll_position and lesson_id:
                return HttpResponseRedirect(f"{reverse('scheduling:schedule')}?scroll_position={scroll_position}&lesson_id={lesson_id}")
            return render(request, 'scheduling/schedule.html', {
                'schedule': schedule,
                'timezone': timezone,
                'messages': messages.get_messages(request)
            })
    return redirect('autorization:student_dashboard' if hasattr(request.user, 'student') else 'scheduling:schedule')
def get_schedule_for_student(student):
    # Логика получения расписания для конкретного студента, например:
    from django.utils import timezone
    from datetime import timedelta
    today = timezone.now().date()
    schedule = {}
    lessons = Lesson.objects.filter(student=student).order_by('time_slot__start_time')
    for lesson in lessons:
        day = lesson.time_slot.start_time.date()
        if day not in schedule:
            schedule[day] = []
        schedule[day].append(lesson)
    return schedule