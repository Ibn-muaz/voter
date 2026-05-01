from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    path('logs/', views.audit_logs, name='logs'),
    path('events/', views.system_events, name='events'),
    path('access/', views.data_access_logs, name='access'),
    path('report/', views.audit_report, name='report'),
]