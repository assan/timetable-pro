#autorization.forms.py
from django import forms
from django.contrib.auth.models import User
from autorization.models import UserProfile
from scheduling.models import Student, Subject, Teacher

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, required=True, label='Имя пользователя')
    password = forms.CharField(widget=forms.PasswordInput, required=True, label='Пароль')

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        if username and password:
            from django.contrib.auth import authenticate
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError('Неверное имя пользователя или пароль.')
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, label='Имя пользователя')
    password = forms.CharField(widget=forms.PasswordInput, required=True, label='Пароль')
    name = forms.CharField(max_length=255, required=True, label='Имя')
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        required=False,
        label='Тип трансмиссии'
    )
    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.all(),
        required=False,
        label='Инструктор'
    )

    class Meta:
        model = UserProfile
        fields = ['role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Устанавливаем порядок полей, чтобы role был первым
        self.fields['role'].widget.attrs.update({'id': 'id_role'})  # Для JavaScript
        # Делаем поле subject обязательным только для ролей student и teacher
        self.fields['subject'].required = False
        self.fields['teacher'].required = False

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Пользователь с таким именем уже существует.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        subject = cleaned_data.get('subject')
        teacher = cleaned_data.get('teacher')

        if role == 'student':
            if not subject:
                self.add_error('subject', 'Выберите тип трансмиссии для курсанта.')
            # Проверяем, что выбранный инструктор соответствует выбранной трансмиссии
            if teacher and subject and teacher.subject != subject:
                self.add_error('teacher', 'Инструктор должен соответствовать выбранному типу трансмиссии.')
        elif role == 'teacher':
            if not subject:
                self.add_error('subject', 'Выберите тип трансмиссии для инструктора.')
        return cleaned_data

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password']
        )
        user_profile = super().save(commit=False)
        user_profile.user = user
        if commit:
            user_profile.save()
            # Создаём запись в Student для роли student
            if user_profile.role == 'student' and not Student.objects.filter(user=user).exists():
                subject = self.cleaned_data.get('subject') or Subject.objects.first()
                teacher = self.cleaned_data.get('teacher')
                if not teacher and Teacher.objects.exists():
                    teacher = Teacher.objects.filter(subject=subject).first()
                Student.objects.create(
                    user=user,
                    name=self.cleaned_data.get('name') or user.username,
                    subject=subject,
                    autodrom_hours=10,
                    city_hours=5,
                    teacher=teacher if teacher else None
                )
            # Создаём запись в Teacher для роли teacher
            elif user_profile.role == 'teacher' and not Teacher.objects.filter(user=user).exists():
                subject = self.cleaned_data.get('subject') or Subject.objects.first()
                Teacher.objects.create(
                    user=user,
                    name=self.cleaned_data.get('name') or user.username,
                    subject=subject
                )
        return user_profile

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'name', 'monday_free_time', 'tuesday_free_time', 'wednesday_free_time',
            'thursday_free_time', 'friday_free_time', 'saturday_free_time', 'sunday_free_time'
        ]
        labels = {
            'name': 'Имя',
            'monday_free_time': 'Свободное время (Понедельник)',
            'tuesday_free_time': 'Свободное время (Вторник)',
            'wednesday_free_time': 'Свободное время (Среда)',
            'thursday_free_time': 'Свободное время (Четверг)',
            'friday_free_time': 'Свободное время (Пятница)',
            'saturday_free_time': 'Свободное время (Суббота)',
            'sunday_free_time': 'Свободное время (Воскресенье)',
        }
        widgets = {
            'monday_free_time': forms.TextInput(attrs={'placeholder': 'Например, 09:00-17:00'}),
            'tuesday_free_time': forms.TextInput(attrs={'placeholder': 'Например, 09:00-17:00'}),
            'wednesday_free_time': forms.TextInput(attrs={'placeholder': 'Например, 09:00-17:00'}),
            'thursday_free_time': forms.TextInput(attrs={'placeholder': 'Например, 09:00-17:00'}),
            'friday_free_time': forms.TextInput(attrs={'placeholder': 'Например, 09:00-17:00'}),
            'saturday_free_time': forms.TextInput(attrs={'placeholder': 'Например, 09:00-17:00'}),
            'sunday_free_time': forms.TextInput(attrs={'placeholder': 'Например, 09:00-17:00'}),
        }

class TeacherProfileForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            'name', 'monday_free_time', 'tuesday_free_time', 'wednesday_free_time',
            'thursday_free_time', 'friday_free_time', 'saturday_free_time', 'sunday_free_time'
        ]
        labels = {
            'name': 'Имя',
            'monday_free_time': 'Свободное время (Понедельник)',
            'tuesday_free_time': 'Свободное время (Вторник)',
            'wednesday_free_time': 'Свободное время (Среда)',
            'thursday_free_time': 'Свободное время (Четверг)',
            'friday_free_time': 'Свободное время (Пятница)',
            'saturday_free_time': 'Свободное время (Суббота)',
            'sunday_free_time': 'Свободное время (Воскресенье)',
        }
        widgets = {
            'monday_free_time': forms.TextInput(attrs={'placeholder': 'Например, 09:00-17:00'}),
            'tuesday_free_time': forms.TextInput(attrs={'placeholder': 'Например, 09:00-17:00'}),
            'wednesday_free_time': forms.TextInput(attrs={'placeholder': 'Например, 09:00-17:00'}),
            'thursday_free_time': forms.TextInput(attrs={'placeholder': 'Например, 09:00-17:00'}),
            'friday_free_time': forms.TextInput(attrs={'placeholder': 'Например, 09:00-17:00'}),
            'saturday_free_time': forms.TextInput(attrs={'placeholder': 'Например, 09:00-17:00'}),
            'sunday_free_time': forms.TextInput(attrs={'placeholder': 'Например, 09:00-17:00'}),
        }