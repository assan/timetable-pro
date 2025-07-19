# scheduling/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.schedule_view, name='schedule'),  # Отображение расписания
    path('calculate/', views.calculate_schedule_view, name='calculate_schedule'),  # Расчет расписания
    path('students/',views.students_view, name='students_view'),
    path("students/edit/<int:id>/", views.edit_student),
    path("students/delete/<int:id>/", views.delete_student),
    path('subjects/', views.subject_view, name='subject_view'),
    path("subjects/edit/<int:id>/", views.edit_subject),
    path("subjects/delete/<int:id>/", views.delete_subject),
    path('teachers/', views.teacher_view, name='teacher_view'),
    path("teachers/edit/<int:id>/", views.edit_teacher),
    path("teachers/delete/<int:id>/", views.delete_teacher),
    path('time_slots/', views.time_slots_view, name='time_slots_view'),
    path("time_slots/edit/<int:id>/", views.edit_time_slot),
    path("time_slots/delete/<int:id>/", views.delete_time_slot),
    path('get-teachers/', views.get_teachers, name='get_teachers'),
]
