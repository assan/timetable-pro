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
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    name = forms.CharField(max_length=255, required=True)
    subject = forms.ModelChoiceField(queryset=Subject.objects.all(), required=True)
    teacher = forms.ModelChoiceField(queryset=Teacher.objects.all(), required=False)

    class Meta:
        model = UserProfile
        fields = ['role']

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Пользователь с таким именем уже существует.")
        return username

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password']
        )
        user_profile = super().save(commit=False)
        user_profile.user = user
        if commit:
            user_profile.save()
            # Если роль student, создаём запись в Student, только если она ещё не существует
            if user_profile.role == 'student' and not Student.objects.filter(user=user).exists():
                subject = self.cleaned_data.get('subject') or Subject.objects.first()
                teacher = self.cleaned_data.get('teacher')
                if not teacher and Teacher.objects.exists():
                    teacher = Teacher.objects.first()
                Student.objects.create(
                    user=user,
                    name=self.cleaned_data.get('name') or user.username,
                    subject=subject,
                    autodrom_hours=10,
                    city_hours=5,
                    teacher=teacher if teacher else None
                )
        return user_profile