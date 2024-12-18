from django.urls import path
from . import views

app_name = 'api_tests'

urlpatterns = [
    path('saludar/', views.saludar, name='saludar'),
    path('saludar_1/', views.SaludarView.as_view(), name='bienvenido'),
    path('saludar_2/', views.SaludarView2.as_view(), name='chau'),
    path('saludar_3/', views.SaludarViewThrottle.as_view(), name='hola'),
    path('check/', views.CheckThrottleData.as_view(), name='check'),
    path('check_oauth/', views.ProtectedViewForOauthApps.as_view(), name='check_oauth'),

]
