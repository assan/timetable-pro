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
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = UserProfile
        fields = ['role', 'name', 'subject', 'teacher']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Проверяем, существует ли instance и связанный user
        if self.instance and hasattr(self.instance, 'user') and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
        # Ограничиваем выбор инструкторов только пользователями с ролью teacher
        self.fields['teacher'].queryset = UserProfile.objects.filter(role='teacher')

    def save(self, commit=True):
        user_profile = super().save(commit=False)
        # Если instance уже имеет user, используем его, иначе создаём новый
        user = self.instance.user if (self.instance and hasattr(self.instance, 'user') and self.instance.user) else User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'] or None
        )
        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])
            user.save()
        user_profile.user = user
        if commit:
            user_profile.save()
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