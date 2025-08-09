from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView
from django.views.generic.edit import FormMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from .forms import *
from .models import UserProfile
from scheduling.models import Student, Teacher, Lesson
from django.http import JsonResponse
from django.views.generic import View
from django.contrib import messages
from django.utils import timezone

def is_admin(user):
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.role == 'admin'

def is_student(user):
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.role == 'student' and Student.objects.filter(user=user).exists()

def is_teacher(user):
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.role == 'teacher'

class LoginView(View):
    template_name = 'autorization/login.html'

    def get(self, request):
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if hasattr(user, 'userprofile'):
                    if user.userprofile.role == 'student':
                        return redirect('autorization:student_dashboard')
                    elif user.userprofile.role == 'teacher':
                        return redirect('autorization:teacher_dashboard')
                    elif user.userprofile.role == 'admin':
                        return redirect('autorization:admin_dashboard')
                return redirect('scheduling:schedule')
        return render(request, self.template_name, {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('autorization:login')


# Главная страница курсната с навигацией
@method_decorator([login_required, user_passes_test(is_student)], name='dispatch')
class StudentDashboardView(View):
    template_name = 'autorization/student_dashboard.html'

    def get(self, request):
        try:
            student = Student.objects.get(user=request.user)
            return render(request, self.template_name, {'student': student})
        except Student.DoesNotExist:
            messages.error(request, 'Профиль курсанта не найден. Обратитесь к администратору.')
            return redirect('autorization:login')


# Управление профилем (свободное время)
@method_decorator([login_required, user_passes_test(is_student)], name='dispatch')
class StudentProfileView(View):
    template_name = 'autorization/student_profile.html'

    def get(self, request):
        student = Student.objects.get(user=request.user)
        form = StudentProfileForm(instance=student)
        return render(request, self.template_name, {'form': form, 'student': student})

    def post(self, request):
        student = Student.objects.get(user=request.user)
        form = StudentProfileForm(request.POST, instance=student)

        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль курсанта успешно обновлён!')
            return redirect('autorization:student_profile')

        return render(request, self.template_name, {'form': form, 'student': student})


# Просмотр расписания и управление занятиями
@method_decorator([login_required, user_passes_test(is_student)], name='dispatch')
class StudentScheduleView(View):
    template_name = 'autorization/student_schedule.html'

    def get(self, request):
        student = Student.objects.get(user=request.user)
        lessons = Lesson.objects.filter(student=student).order_by('lesson_time')
        return render(request, self.template_name, {
            'student': student,
            'lessons': lessons,
            'now': timezone.now()
        })

    def post(self, request):
        student = Student.objects.get(user=request.user)
        lessons = Lesson.objects.filter(student=student).order_by('lesson_time')

        for key, value in request.POST.items():
            if key.startswith('confirm_') and value == '1':
                lesson_id = key.replace('confirm_', '')
                try:
                    lesson = Lesson.objects.get(id=lesson_id, student=student, status=0)
                    lesson.status = 1
                    lesson.save()
                    messages.success(request, f'Занятие с ID {lesson_id} подтверждено.')
                except Lesson.DoesNotExist:
                    messages.error(request, f'Ошибка: Занятие {lesson_id} не найдено или не может быть подтверждено.')
            elif key.startswith('cancel_') and value == '3':
                lesson_id = key.replace('cancel_', '')
                try:
                    lesson = Lesson.objects.get(id=lesson_id, student=student, status=1)
                    if not lesson.lesson_time or (lesson.lesson_time - timezone.now()).total_seconds() / 3600 > 24:
                        lesson.status = 3
                        lesson.save()
                        messages.success(request, f'Занятие с ID {lesson_id} отменено.')
                    else:
                        messages.error(request, f'Ошибка: Отмена невозможна (менее 24 часов до {lesson.lesson_time}).')
                except Lesson.DoesNotExist:
                    messages.error(request, f'Ошибка: Занятие {lesson_id} не найдено или не может быть отменено.')

        return render(request, self.template_name, {
            'student': student,
            'lessons': lessons,
            'now': timezone.now()
        })

# Главная страница инструктора с навигацией
@method_decorator([login_required, user_passes_test(is_teacher)], name='dispatch')
class TeacherDashboardView(View):
    template_name = 'autorization/teacher_dashboard.html'

    def get(self, request):
        teacher = Teacher.objects.get(user=request.user)
        return render(request, self.template_name, {'teacher': teacher})


# Управление профилем (свободное время)
@method_decorator([login_required, user_passes_test(is_teacher)], name='dispatch')
class TeacherProfileView(View):
    template_name = 'autorization/teacher_profile.html'

    def get(self, request):
        teacher = Teacher.objects.get(user=request.user)
        form = TeacherProfileForm(instance=teacher)
        return render(request, self.template_name, {'form': form, 'teacher': teacher})

    def post(self, request):
        teacher = Teacher.objects.get(user=request.user)
        form = TeacherProfileForm(request.POST, instance=teacher)

        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль инструктора успешно обновлён!')
            return redirect('autorization:teacher_profile')  # Используем правильное имя маршрута


# Отметка посещенных уроков
@method_decorator([login_required, user_passes_test(is_teacher)], name='dispatch')
class TeacherLessonsView(View):
    template_name = 'autorization/teacher_lessons.html'

    def get(self, request):
        teacher = Teacher.objects.get(user=request.user)
        lessons = Lesson.objects.filter(teacher=teacher).order_by('lesson_time')
        return render(request, self.template_name, {
            'teacher': teacher,
            'lessons': lessons,
            'now': timezone.now()
        })

    def post(self, request):
        teacher = Teacher.objects.get(user=request.user)
        lessons = Lesson.objects.filter(teacher=teacher).order_by('lesson_time')

        for key, value in request.POST.items():
            if key.startswith('complete_') and value == '2':
                lesson_id = key.replace('complete_', '')
                lesson_type_key = f'lesson_type_{lesson_id}'
                lesson_type = request.POST.get(lesson_type_key)

                if lesson_type not in ['autodrom', 'city']:
                    messages.error(request, f'Ошибка: Не указан тип занятия для урока {lesson_id}.')
                    continue

                try:
                    lesson = Lesson.objects.get(id=lesson_id, teacher=teacher, status=1)
                    lesson.status = 2
                    lesson.lesson_type = lesson_type
                    lesson.save()

                    student = lesson.student
                    time_slot = lesson.time_slot
                    duration_hours = (time_slot.end_minutes - time_slot.start_minutes) / 60.0

                    if duration_hours <= 0:
                        messages.error(request, f'Ошибка: Неверная длительность занятия для {lesson.student.name}.')
                        continue

                    if lesson_type == 'autodrom':
                        student.autodrom_hours = max((student.autodrom_hours or 0) - duration_hours, 0)
                    elif lesson_type == 'city':
                        student.city_hours = max((student.city_hours or 0) - duration_hours, 0)
                    student.save()

                    messages.success(request,
                                     f'Занятие с {lesson.student.name} отмечено как проведённое ({lesson.get_lesson_type_display()}).')
                except Lesson.DoesNotExist:
                    messages.error(request, f'Ошибка: Занятие {lesson_id} не найдено или не может быть отмечено.')

        return render(request, self.template_name, {
            'teacher': teacher,
            'lessons': lessons,
            'now': timezone.now()
        })


@method_decorator([login_required, user_passes_test(is_admin)], name='dispatch')
class AdminDashboardView(View):
    def get(self, request):
        form = UserProfileForm()
        users = UserProfile.objects.filter(user__isnull=False)
        return render(request, 'autorization/admin_dashboard.html', {'form': form, 'users': users})

    def post(self, request):
        form = UserProfileForm(request.POST)
        if form.is_valid():
            user_profile = form.save(commit=False)
            role = form.cleaned_data['role']
            name = form.cleaned_data['name']
            subject = form.cleaned_data.get('subject')
            teacher_profile = form.cleaned_data.get('teacher')

            user_profile.save()

            if role == 'student':
                try:
                    teacher = Teacher.objects.get(user=teacher_profile.user)
                except Teacher.DoesNotExist:
                    messages.error(request, 'Ошибка: Выбранный инструктор не имеет профиля Teacher.')
                    return render(request, 'autorization/admin_dashboard.html',
                                  {'form': form, 'users': UserProfile.objects.filter(user__isnull=False)})

                Student.objects.create(
                    user=user_profile.user,
                    name=name,
                    subject=subject,
                    teacher=teacher
                )
            elif role == 'teacher':
                Teacher.objects.create(
                    user=user_profile.user,
                    name=name,
                    subject=subject
                )

            role_display = dict(UserProfile.ROLES).get(role, 'Курсант')
            messages.success(request, f"{role_display} успешно создан!")
            return redirect('autorization:admin_dashboard')  # Редирект после успеха

        # Если форма невалидна, рендерим с ошибками
        users = UserProfile.objects.filter(user__isnull=False)
        return render(request, 'autorization/admin_dashboard.html', {'form': form, 'users': users})

@method_decorator([login_required, user_passes_test(is_admin)], name='dispatch')
class EditUserView(View):
    def get(self, request, user_id):
        user_profile = get_object_or_404(UserProfile, id=user_id)
        form = UserProfileForm(instance=user_profile)
        return render(request, 'autorization/edit_user.html', {'form': form, 'user_id': user_id})

    def post(self, request, user_id):
        user_profile = get_object_or_404(UserProfile, id=user_id)
        form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, f"Пользователь {user_profile.user.username} успешно обновлён!")
            return redirect('autorization:admin_dashboard')
        return render(request, 'autorization/edit_user.html', {'form': form, 'user_id': user_id})

@method_decorator([login_required, user_passes_test(is_admin)], name='dispatch')
class DeleteUserView(View):
    def post(self, request, user_id):
        user_profile = get_object_or_404(UserProfile, id=user_id)
        username = user_profile.user.username
        user_profile.user.delete()  # Удаляем связанного пользователя
        user_profile.delete()  # Удаляем профиль
        messages.success(request, f"Пользователь {username} успешно удалён!")
        return redirect('autorization:admin_dashboard')

def get_teachers_by_subject(request, subject_id):
    teachers = UserProfile.objects.filter(
        role='teacher',
        user__teacher__subject_id=subject_id
    ).values('id', 'name')
    return JsonResponse({'teachers': list(teachers)})

