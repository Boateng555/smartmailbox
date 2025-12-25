from django.urls import path
from . import views

app_name = 'firmware'

urlpatterns = [
    path('latest/', views.latest_firmware, name='latest_firmware'),
]







