# autorization/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from autorization.models import UserProfile
from scheduling.models import Student, Subject

@receiver(post_save, sender=UserProfile)
def create_student_for_user(sender, instance, created, **kwargs):
    if created and instance.role == 'student' and not Student.objects.filter(user=instance.user).exists():
        subject = Subject.objects.first()  # Запасной вариант, если subject не передан
        Student.objects.create(
            user=instance.user,
            name=instance.user.username,
            subject=subject,
            autodrom_hours=10,
            city_hours=5
        )