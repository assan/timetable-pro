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
            'now': timezone.now()
        })

    def post(self, request):
        student = Student.objects.get(user=request.user)
        form = StudentProfileForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль курсанта успешно обновлён!')
            return redirect('autorization:student_dashboard')
        lessons = Lesson.objects.filter(student=student).order_by('lesson_time')
        return (render(request, self.template_name, {
            'form': form,
            'student': student,
            'lessons': lessons,
            'now': timezone.now()
        })
@method_decorator([login_required, user_passes_test(is_teacher)], name='dispatch'))
class TeacherDashboardView(View):
    template_name = 'autorization/teacher_dashboard.html'

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
            return redirect('autorization:teacher_dashboard')
        return render(request, self.template_name, {'form': form, 'teacher': teacher})

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

@login_required
def confirm_lessons(request):
    if request.method == 'POST':
        student = request.user.student if hasattr(request.user, 'student') else None
        if not student:
            messages.error(request, 'Вы не являетесь курсантом.')
            return redirect('autorization:student_dashboard')  # Или другая страница по умолчанию

        for key, value in request.POST.items():
            if key.startswith('confirm_'):
                lesson_id = key.replace('confirm_', '')
                try:
                    lesson = Lesson.objects.get(id=lesson_id, student=student)
                    if lesson.status == 0 and int(value) == 1:  # Только из scheduled в confirmed
                        lesson.status = 1
                        lesson.save()
                        print(f"Confirmed lesson {lesson_id}")
                        messages.success(request, f'Занятие {lesson_id} подтверждено.')
                except Lesson.DoesNotExist:
                    messages.error(request, f'Занятие {lesson_id} не найдено.')
            elif key.startswith('cancel_'):
                lesson_id = key.replace('cancel_', '')
                try:
                    lesson = Lesson.objects.get(id=lesson_id, student=student)
                    if lesson.status == 0 and timezone.now() < lesson.lesson_time - timezone.timedelta(hours=24):
                        lesson.status = 3
                        lesson.save()
                        messages.success(request, f'Занятие {lesson_id} отменено.')
                    else:
                        messages.error(request, f'Отмена занятия {lesson_id} невозможна (менее 24 часов или не запланировано).')
                except Lesson.DoesNotExist:
                    messages.error(request, f'Занятие {lesson_id} не найдено.')
            elif key == 'save':  # Обработка кнопки "Сохранить изменения"
                pass  # Можно добавить дополнительную логику, если нужно

        # Получаем обновлённые данные для рендеринга
        form = StudentProfileForm(instance=student)
        lessons = Lesson.objects.filter(student=student).order_by('lesson_time')
        return render(request, 'autorization/student_dashboard.html', {
            'form': form,
            'student': student,
            'lessons': lessons,
            'now': timezone.now()
        })
    return redirect('autorization:student_dashboard')  # Для GET-запросов перенаправляем на страницу