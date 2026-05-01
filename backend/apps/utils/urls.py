from django.urls import path
from . import views

app_name = 'utils'

urlpatterns = [
    path('captcha/', views.generate_captcha, name='captcha'),
    path('states/', views.get_states, name='states'),
    path('lgas/<str:state_code>/', views.get_lgas, name='lgas'),
]