"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    # El Admin y las vistas públicas pasan por el mismo proyecto Django.
    path('admin/', admin.site.urls),
    # Vercel llega a esta raíz y el usuario termina en el catálogo.
    path('', RedirectView.as_view(pattern_name='producto_list', permanent=False)),
    # include delega las rutas del inventario a sus vistas, que consultan Supabase
    # mediante el ORM; no existe una conexión directa del navegador a Supabase.
    path('', include('inventario.urls')),  # Conecta todas las URLs de inventario
]
