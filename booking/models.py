# booking/models.py
from django.db import models
from scheduling.models import Student, Teacher, Subject, TimeSlot, Lesson


class Booking(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE
    )
    # Конкретный временной слот (из существующих TimeSlot)
    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.CASCADE
    )
    # Конкретная дата бронирования
    date = models.DateField()
    # День недели (для удобства)
    day_of_week = models.IntegerField(choices=Lesson.DAYS_OF_WEEK)

    # Связь с созданным уроком (если бронь подтверждена)
    lesson = models.OneToOneField(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='booking'
    )

    STATUS_CHOICES = (
        (0, 'Ожидает'),
        (1, 'Подтверждено'),
        (2, 'Отменено'),
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Один слот на одну дату и одного инструктора — только одна бронь
        unique_together = ('teacher', 'date', 'time_slot')
        ordering = ['date', 'time_slot__start_minutes']

    def __str__(self):
        return f"{self.student.name} → {self.teacher.name} ({self.date} {self.time_slot})"