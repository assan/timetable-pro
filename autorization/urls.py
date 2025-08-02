from django.urls import path
from .views import *
app_name = 'autorization'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('student/profile/', StudentProfileView.as_view(), name='student_profile'),
    path('student/schedule/', StudentScheduleView.as_view(), name='student_schedule'),
    path('student/dashboard/', StudentDashboardView.as_view(), name='student_dashboard'),
    path('teacher/dashboard/', TeacherDashboardView.as_view(), name='teacher_dashboard'),
    path('teacher/profile/', TeacherProfileView.as_view(), name='teacher_profile'),
    path('teacher/lessons/', TeacherLessonsView.as_view(), name='teacher_lessons'),
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('get_teachers_by_subject/<int:subject_id>/', get_teachers_by_subject, name='get_teachers_by_subject'),
    path('edit_user/<int:user_id>/', EditUserView.as_view(), name='edit_user'),
    path('delete_user/<int:user_id>/', DeleteUserView.as_view(), name='delete_user'),

]