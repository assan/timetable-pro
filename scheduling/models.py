# templates/models.py

from django.db import models
class Subject(models.Model):
    name = models.CharField(max_length=20)
    def __str__(self):
        return self.name
class Teacher(models.Model):
    name = models.CharField(max_length=100)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, default=1)
    def __str__(self):
        return self.name

class Student(models.Model):
    name = models.CharField(max_length=50)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher=models.ForeignKey(Teacher,on_delete=models.CASCADE)
    times_per_week=models.IntegerField(default=7)
    monday_free_time = models.CharField(max_length=100, default="", null = True, blank = True)
    tuesday_free_time = models.CharField(max_length=100, default="", null = True, blank = True)
    wednesday_free_time = models.CharField(max_length=100, default="", null = True, blank = True)
    thursday_free_time = models.CharField(max_length=100, default="", null = True, blank = True)
    friday_free_time = models.CharField(max_length=100, default="", null = True, blank = True)
    saturday_free_time = models.CharField(max_length=100, default="", null = True, blank = True)
    sunday_free_time = models.CharField(max_length=100, default="", null = True, blank = True)

    def __str__(self):
        return self.name

class TimeSlot(models.Model):
    start_time = models.CharField(max_length=20)
    end_time = models.CharField(max_length=20)
    start_minutes = models.IntegerField(default=0)  # время старта в минутах
    end_minutes = models.IntegerField(default=0)  # время окончания в минутах

    def __str__(self):
        return f"{self.start_time} - {self.end_time}"

class Availability(models.Model):
    DAYS_OF_WEEK = (
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE,default=1)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    subject= models.ForeignKey(Subject, on_delete=models.CASCADE, default=1)
    available = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student} - {self.get_day_of_week_display()} - {self.time_slot} - {'Available' if self.available else 'Not Available'}"

class Lesson(models.Model):
    DAYS_OF_WEEK = (
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.teacher} - {self.get_day_of_week_display()} - {self.time_slot}"
