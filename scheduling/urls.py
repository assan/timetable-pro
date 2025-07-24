from django.urls import path
from .views import (
    StudentListCreateView, StudentUpdateView, StudentDeleteView,
    SubjectListCreateView, SubjectUpdateView, SubjectDeleteView,
    TeacherListCreateView, TeacherUpdateView, TeacherDeleteView,
    TimeSlotListCreateView, TimeSlotUpdateView, TimeSlotDeleteView,
    CalculateScheduleView, ScheduleView, get_teachers, mark_attendance
)

app_name = 'scheduling'

urlpatterns = [
    path('students/', StudentListCreateView.as_view(), name='students'),
    path('students/edit/<int:pk>/', StudentUpdateView.as_view(), name='student_edit'),
    path('students/delete/<int:pk>/', StudentDeleteView.as_view(), name='student_delete'),
    path('subjects/', SubjectListCreateView.as_view(), name='subjects'),
    path('subjects/edit/<int:pk>/', SubjectUpdateView.as_view(), name='subject_edit'),
    path('subjects/delete/<int:pk>/', SubjectDeleteView.as_view(), name='subject_delete'),
    path('teachers/', TeacherListCreateView.as_view(), name='teachers'),
    path('teachers/edit/<int:pk>/', TeacherUpdateView.as_view(), name='teacher_edit'),
    path('teachers/delete/<int:pk>/', TeacherDeleteView.as_view(), name='teacher_delete'),
    path('time_slots/', TimeSlotListCreateView.as_view(), name='time_slots'),
    path('time_slots/edit/<int:pk>/', TimeSlotUpdateView.as_view(), name='time_slot_edit'),
    path('time_slots/delete/<int:pk>/', TimeSlotDeleteView.as_view(), name='time_slot_delete'),
    path('calculate/', CalculateScheduleView.as_view(), name='calculate_schedule'),
    path('schedule/', ScheduleView.as_view(), name='schedule'),
    path('teachers/get/', get_teachers, name='get_teachers'),
    path('attendance/', mark_attendance, name='mark_attendance'),
]