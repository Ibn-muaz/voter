from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('generate/', views.generate_report, name='generate'),
    path('download/<int:report_id>/', views.download_report, name='download'),
    path('dashboard/', views.dashboard, name='dashboard'),
]