from django import forms
from django.contrib.auth.models import User
from .models import UserProfile
from scheduling.models import Student, Teacher, Subject

class UserProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=150, label="Имя пользователя")
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")
    role = forms.ChoiceField(choices=UserProfile.ROLES, label="Роль")
    name = forms.CharField(max_length=100, label="Имя")
    subject = forms.ModelChoiceField(queryset=Subject.objects.all(), label="Трансмиссия", required=False)
    teacher = forms.ModelChoiceField(queryset=Teacher.objects.all(), label="Инструктор", required=False)

    class Meta:
        model = UserProfile
        fields = ['role']

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password']
        )
        user_profile = super().save(commit=False)
        user_profile.user = user
        if commit:
            user_profile.save()
            if user_profile.role == 'student':
                Student.objects.create(
                    user=user,
                    name=self.cleaned_data['name'],
                    subject=self.cleaned_data['subject'],
                    teacher=self.cleaned_data['teacher']
                )
            elif user_profile.role == 'teacher':
                Teacher.objects.create(
                    user=user,
                    name=self.cleaned_data['name'],
                    subject=self.cleaned_data['subject']
                )
        return user_profile