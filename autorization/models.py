#autorization.models.py
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLES = (
        ('admin', 'Администратор'),
        ('student', 'Курсант'),
        ('teacher', 'Инструктор'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLES, default='student')

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"