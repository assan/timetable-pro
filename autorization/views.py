from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView
from django.views.generic.edit import FormMixin
from django.shortcuts import render, redirect
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
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.role == 'student'

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

@method_decorator([login_required, user_passes_test(is_student)], name='dispatch')
class StudentDashboardView(View):
    template_name = 'autorization/student_dashboard.html'

    def get(self, request):
        student = Student.objects.get(user=request.user)
        form = StudentProfileForm(instance=student)
        lessons = Lesson.objects.filter(student=student).order_by('lesson_time')
        return render(request, self.template_name, {
            'form': form,
            'student': student,
            'lessons': lessons,
            'now': timezone.now()  # Гарантируем передачу now
        })

    def post(self, request):
        student = Student.objects.get(user=request.user)
        form = StudentProfileForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль курсанта успешно обновлён!')
            return redirect('autorization:student_dashboard')
        lessons = Lesson.objects.filter(student=student).order_by('lesson_time')
        return render(request, self.template_name, {
            'form': form,
            'student': student,
            'lessons': lessons,
            'now': timezone.now()  # Передаём now и при POST
        })


@method_decorator([login_required, user_passes_test(is_teacher)], name='dispatch')
class TeacherDashboardView(View):
    template_name = 'autorization/teacher_dashboard.html'

    def get(self, request):
        teacher = Teacher.objects.get(user=request.user)
        form = TeacherProfileForm(instance=teacher)
        lessons = Lesson.objects.filter(teacher=teacher).order_by('lesson_time')
        return render(request, self.template_name, {
            'form': form,
            'teacher': teacher,
            'lessons': lessons,
            'now': timezone.now()
        })

    def post(self, request):
        teacher = Teacher.objects.get(user=request.user)
        form = TeacherProfileForm(request.POST, instance=teacher)

        if 'save_profile' in request.POST and form.is_valid():
            form.save()
            messages.success(request, 'Профиль инструктора успешно обновлён!')
            return redirect('autorization:teacher_dashboard')

        # Обработка изменения статуса занятий
        for key, value in request.POST.items():
            if key.startswith('complete_') and value == '2':
                lesson_id = key.replace('complete_', '')
                lesson_type_key = f'lesson_type_{lesson_id}'
                lesson_type = request.POST.get(lesson_type_key)

                if not lesson_type or lesson_type not in ['autodrom', 'city']:
                    messages.error(request, f'Ошибка: Не указан или неверный тип занятия для урока {lesson_id}.')
                    continue

                try:
                    lesson = Lesson.objects.get(id=lesson_id, teacher=teacher,
                                                status=1)  # Только подтверждённые занятия
                    lesson.status = 2  # Отметка как проведённое
                    lesson.lesson_type = lesson_type  # Установка типа занятия
                    lesson.save()

                    # Обновление часов ученика
                    student = lesson.student
                    time_slot = lesson.time_slot
                    duration_hours = (time_slot.end_minutes - time_slot.start_minutes) / 60.0  # Длительность в часах

                    if duration_hours <= 0:
                        messages.error(request, f'Ошибка: Неверная длительность занятия для {lesson.student}.')
                        continue

                    if lesson_type == 'autodrom':
                        student.autodrom_hours = (student.autodrom_hours or 0) + duration_hours
                    elif lesson_type == 'city':
                        student.city_hours = (student.city_hours or 0) + duration_hours
                    student.save()

                    messages.success(request,
                                     f'Занятие с {lesson.student} отмечено как проведённое ({lesson.get_lesson_type_display()}).')
                except Lesson.DoesNotExist:
                    messages.error(request, f'Ошибка: Занятие {lesson_id} не найдено или не может быть отмечено.')

        lessons = Lesson.objects.filter(teacher=teacher).order_by('lesson_time')
        return render(request, self.template_name, {
            'form': form,
            'teacher': teacher,
            'lessons': lessons,
            'now': timezone.now()
        })
@method_decorator([login_required, user_passes_test(is_admin)], name='dispatch')
class AdminDashboardView(View):
    def get(self, request):
        form = UserProfileForm()
        users = UserProfile.objects.all()
        return render(request, 'autorization/admin_dashboard.html', {'form': form, 'users': users})

    def post(self, request):
        print(request.POST)
        form = UserProfileForm(request.POST)
        if form.is_valid():
            print(form.cleaned_data)
            form.save()
            role_display = dict(UserProfile.ROLES).get(form.cleaned_data['role'], 'Пользователь')
            messages.success(request, f"{role_display} успешно создан!")
            return redirect('autorization:admin_dashboard')
        users = UserProfile.objects.all()
        return render(request, 'autorization/admin_dashboard.html', {'form': form, 'users': users})

def get_teachers_by_subject(request, subject_id):
    teachers = Teacher.objects.filter(subject_id=subject_id).values('id', 'name')
    return JsonResponse({'teachers': list(teachers)})

