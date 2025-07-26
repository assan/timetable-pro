from django.urls import path
from .views import LoginView, logout_view, StudentDashboardView, TeacherDashboardView, AdminDashboardView
from .views import get_teachers_by_subject
app_name = 'autorization'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('student/dashboard/', StudentDashboardView.as_view(), name='student_dashboard'),
    path('teacher/dashboard/', TeacherDashboardView.as_view(), name='teacher_dashboard'),
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('get_teachers_by_subject/<int:subject_id>/', get_teachers_by_subject, name='get_teachers_by_subject'),
]