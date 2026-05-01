from django.urls import path
from . import views

app_name = 'registration'

urlpatterns = [
    path('', views.registration_wizard, name='wizard'),
    path('step/<int:step>/', views.registration_wizard, name='wizard'),
    path('success/<int:registration_id>/', views.registration_success, name='success'),
    path('rejected/<int:registration_id>/', views.registration_rejected, name='rejected'),
    path('list/', views.registration_list, name='list'),
    path('status/<int:registration_id>/', views.registration_status, name='status'),
    path('detail/<int:registration_id>/', views.registration_detail, name='detail'),
    path('search/', views.registration_search, name='search'),
    path('lgas/', views.get_lgas_for_state, name='lgas'),
    path('bulk-upload/', views.bulk_registration_upload, name='bulk_upload'),
    path('download-tvc/<int:registration_id>/', views.download_tvc, name='download_tvc'),
]