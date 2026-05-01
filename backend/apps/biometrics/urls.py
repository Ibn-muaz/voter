from django.urls import path
from . import views

app_name = 'biometrics'

urlpatterns = [
    path('capture/', views.capture_biometric, name='capture'),
    path('verify/<int:biometric_id>/', views.verify_biometric, name='verify'),
    path('match/', views.match_biometric, name='match'),
]