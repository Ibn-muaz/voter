from django.urls import path
from . import views

app_name = 'ai_engine'

urlpatterns = [
    path('verify/', views.verify_registration, name='verify'),
    path('status/<uuid:verification_id>/', views.verification_status, name='status'),
    path('results/<uuid:verification_id>/', views.verification_results, name='results'),
]