# templates/forms.py

from django import forms
from django.contrib.auth.models import User
from .models import *

class StudentForm(forms.ModelForm):
    subject = forms.ModelChoiceField(queryset=Subject.objects.all(), label = "Трансмиссия")
    teacher=forms.ModelChoiceField(queryset=Teacher.objects.all(), label ="Инструктор")
    class Meta:
        model= Student
        fields='__all__'
        labels = {'name': 'Имя курсанта',
                  'subject':'Тип коробки передач',
                  'teacher':'Инструктор',
                  'city_hours':'Часы вождения в городе',
                  'autodrom_hours':'Часы вождения на автодроме',
                  'times_per_week':'Максимальное количество занятий в неделю',
                  'monday_free_time':"Свободное время в понедельник",
                  'tuesday_free_time':"Свободное время во вторник",
                  'wednesday_free_time':"Свободное время в среду",
                  'thursday_free_time':"Свободное время в четверг",
                  'friday_free_time':"Свободное время в пятницу",
                  'saturday_free_time':"Свободное время в субботу",
                  'sunday_free_time':"Свободное время в воскресенье"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].queryset = Teacher.objects.none()

        if 'subject' in self.data:
            try:
                subject_id = int(self.data.get('subject'))
                self.fields['teacher'].queryset = Teacher.objects.filter(subject_id=subject_id).order_by('name')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty Teacher queryset
        elif self.instance.pk:
            self.fields['teacher'].queryset = self.instance.subject.teacher_set.order_by('name')
class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields=['name']
        labels={'name':'Тип трансмиссии'}
class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields='__all__'
        labels = {'name': 'Имя инструктора',
                  'subject': 'Трансмиссия на учёбной машине',
                  'monday_free_time': "Свободное время в понедельник",
                  'tuesday_free_time': "Свободное время во вторник",
                  'wednesday_free_time': "Свободное время в среду",
                  'thursday_free_time': "Свободное время в четверг",
                  'friday_free_time': "Свободное время в пятницу",
                  'saturday_free_time': "Свободное время в субботу",
                  'sunday_free_time': "Свободное время в воскресенье"}
class TimeSlotForm(forms.ModelForm):
    class Meta:
        model = TimeSlot
        fields = ['start_time','end_time']
        labels={'start_time':'Время начала занятия','end_time':'Время конца занятия'}

