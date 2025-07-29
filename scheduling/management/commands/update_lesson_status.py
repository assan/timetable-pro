from django.core.management.base import BaseCommand
from scheduling.models import Lesson

class Command(BaseCommand):
    help = 'Updates Lesson status based on old fields'

    def handle(self, *args, **options):
        for lesson in Lesson.objects.all():
            if hasattr(lesson, 'is_attended'):
                if lesson.is_attended:
                    lesson.status = 2
                elif lesson.is_confirmed:
                    lesson.status = 1
                elif hasattr(lesson, 'is_cancelled') and lesson.is_cancelled:
                    lesson.status = 3
                else:
                    lesson.status = 0
                lesson.save()
        self.stdout.write(self.style.SUCCESS('Successfully updated Lesson statuses'))