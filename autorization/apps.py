from django.apps import AppConfig

class AutorizationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'autorization'

    # def ready(self):
    #     import autorization.signals  # Подключаем сигналы