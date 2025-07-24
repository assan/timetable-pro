from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import View, UpdateView, ListView
from django.views.generic.edit import FormMixin
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.urls import reverse_lazy
from .models import UserProfile
from .forms import UserProfileForm
from scheduling.models import Student, Teacher

# Проверка роли пользователя
def is_admin(user):
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.role == 'admin'

def is_student(user):
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.role == 'student'

def is_teacher(user):
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.role == 'teacher'

# Декораторы для защиты представлений
decorators_student = [login_required, user_passes_test(is_student)]
decorators_teacher = [login_required, user_passes_test(is_teacher)]
decorators_admin = [login_required, user_passes_test(is_admin)]

# Логин
class LoginView(View):
    template_name = 'autorization/login.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if hasattr(user, 'userprofile'):
                if user.userprofile.role == 'admin':
                    return redirect('autorization:admin_dashboard')
                elif user.userprofile.role == 'student':
                    return redirect('autorization:student_dashboard')
                elif user.userprofile.role == 'teacher':
                    return redirect('autorization:teacher_dashboard')
            return redirect('scheduling:schedule')
        return render(request, self.template_name, {'error': 'Неверные данные'})

# Логаут
def logout_view(request):
    logout(request)
    return redirect('autorization:login')

# Личный кабинет курсанта
@method_decorator(decorators_student, name='dispatch')
class StudentDashboardView(UpdateView):
    model = Student
    fields = ['monday_free_time', 'tuesday_free_time', 'wednesday_free_time', 'thursday_free_time',
              'friday_free_time', 'saturday_free_time', 'sunday_free_time']
    template_name = 'autorization/student_dashboard.html'
    success_url = reverse_lazy('autorization:student_dashboard')

    def get_object(self):
        return Student.objects.get(user=self.request.user)

# Личный кабинет инструктора
@method_decorator(decorators_teacher, name='dispatch')
class TeacherDashboardView(UpdateView):
    model = Teacher
    fields = ['monday_free_time', 'tuesday_free_time', 'wednesday_free_time', 'thursday_free_time',
              'friday_free_time', 'saturday_free_time', 'sunday_free_time']
    template_name = 'autorization/teacher_dashboard.html'
    success_url = reverse_lazy('autorization:teacher_dashboard')

    def get_object(self):
        return Teacher.objects.get(user=self.request.user)

# Панель администратора
@method_decorator(decorators_admin, name='dispatch')
class AdminDashboardView(ListView, FormMixin):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'autorization/admin_dashboard.html'
    context_object_name = 'users'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            form.save()
            return redirect('autorization:admin_dashboard')
        return self.form_invalid(form)