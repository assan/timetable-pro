# scheduling/management/commands/update_lessons.py
from django.core.management.base import BaseCommand
from scheduling.models import Lesson, Student

class Command(BaseCommand):
    help = 'Updates lessons to link with students'

    def handle(self, *args, **options):
        students = Student.objects.all()
        for student in students:
            lessons = Lesson.objects.filter(student__isnull=True)  # Уроки без студента
            for lesson in lessons:
                lesson.student = student
                lesson.save()
        self.stdout.write(self.style.SUCCESS('Successfully updated lessons'))