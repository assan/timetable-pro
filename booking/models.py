# booking/models.py
from django.db import models
from django.conf import settings
from scheduling.models import *
class Booking(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    # Ссылка на вашу существующую модель слота/урока
    # Например: lesson = models.ForeignKey('scheduling.Lesson', on_delete=models.CASCADE)
    lesson = Lesson(on_delete=models.CASCADE)
    slot_datetime = TimeSlot(on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        # Гарантирует, что на один слот не будет двух броней
        unique_together = ('slot_datetime',) 
        # Или, если у вас есть модель слота:
        # unique_together = ('lesson',)

    def __str__(self):
        return f"{self.student} - {self.slot_datetime}"