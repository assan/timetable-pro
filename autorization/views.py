from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView
from django.views.generic.edit import FormMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from .forms import LoginForm, UserProfileForm
from .models import UserProfile
from scheduling.models import Student, Teacher, Lesson

def is_admin(user):
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.role == 'admin'

def is_student(user):
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.role == 'student'

def is_teacher(user):
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.role == 'teacher'

class LoginView(TemplateView):
    template_name = 'autorization/login.html'

    def post(self, request, *args, **kwargs):
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
class StudentDashboardView(TemplateView):
    template_name = 'autorization/student_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = Student.objects.get(user=self.request.user)
        lessons = Lesson.objects.filter(student=student)
        schedule = {i: [] for i in range(7)}
        for lesson in lessons:
            schedule[lesson.day_of_week].append(lesson)
        context['schedule'] = schedule
        return context

@method_decorator([login_required, user_passes_test(is_teacher)], name='dispatch')
class TeacherDashboardView(TemplateView):
    template_name = 'autorization/teacher_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = Teacher.objects.get(user=self.request.user)
        lessons = Lesson.objects.filter(teacher=teacher)
        schedule = {i: [] for i in range(7)}
        for lesson in lessons:
            schedule[lesson.day_of_week].append(lesson)
        context['schedule'] = schedule
        return context

@method_decorator([login_required, user_passes_test(is_admin)], name='dispatch')
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