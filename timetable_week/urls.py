from django.contrib import admin
from django.urls import path, include
from scheduling.views import ScheduleView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('scheduling/', include('scheduling.urls')),
    path('autorization/', include('autorization.urls')),
    path('', ScheduleView.as_view(), name='home'),
]