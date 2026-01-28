#PORTAL/martillo_vil/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Esta es la UNICA línea que necesitas para conectar tu app
    path('', include('dashboard.urls')), 
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)