from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('upload/', views.upload_document, name='upload'),
    path('verify/<int:document_id>/', views.verify_document, name='verify'),
    path('download/<int:document_id>/', views.download_document, name='download'),
]