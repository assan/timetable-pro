from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from autorization.models import UserProfile
from scheduling.models import Student, Subject

@receiver(post_save, sender=UserProfile)
def create_student_for_user(sender, instance, created, **kwargs):
    if created and instance.role == 'student':
        # Проверяем, существует ли уже запись Student для этого пользователя
        if not Student.objects.filter(user=instance.user).exists():
            # Получаем или создаём предмет по умолчанию (например, "Механика")
            subject, _ = Subject.objects.get_or_create(name='Механика')
            # Создаём запись Student
            Student.objects.create(
                user=instance.user,
                name=instance.user.username,  # Или другое имя, например, из формы
                subject=subject,
                autodrom_hours=10,  # Значения по умолчанию
                city_hours=5
            )