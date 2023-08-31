from django.conf.urls.static import static
from django.contrib import admin

from django.urls import path, include
from tas import settings
from transport.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('transport.urls')),
    path('create/', include('pdfview.urls', namespace='pdfview')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = pageNotFound