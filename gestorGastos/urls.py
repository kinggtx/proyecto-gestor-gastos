# gestion_gastos_personales/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('aplicacion.urls')),  # Incluye las URLs de tu app
]