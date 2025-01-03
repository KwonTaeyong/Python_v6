from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic import TemplateView
from . import views


urlpatterns = [
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type='text/plain')),
    path('', views.imglist, name='imglist'),
    path('as/img/imgupload', views.imgupload, name='imgupload'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
