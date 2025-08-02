#autorization.models.py
from django.db import models
from django.contrib.auth.models import User
from scheduling.models import *

class UserProfile(models.Model):
    ROLES = (
        ('admin', 'Администратор'),
        ('student', 'Курсант'),
        ('teacher', 'Инструктор'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLES, default='student')
    name = models.CharField(max_length=100, blank=True, null=True)  # Поле для имени
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)  # Тип трансмиссии
    teacher = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role': 'teacher'})  # Инструктор

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"