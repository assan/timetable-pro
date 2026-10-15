# booking/urls.py
from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('free-slots/', views.free_slots_view, name='free_slots'),
    path('book/', views.book_slot, name='book_slot'),
]