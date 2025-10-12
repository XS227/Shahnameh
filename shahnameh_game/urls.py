"""
URL configuration for shahnameh_game project.

The `urlpatterns` list routes URLs to views. For more information see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.marketing_home, name='index'),
    path('api/', include('core.urls')),
    path('docs/legacy-overview/', core_views.legacy_repo_overview, name='legacy-overview'),
    path('docs/whitepaper/', core_views.whitepaper_overview, name='whitepaper'),
    path('docs/roadmap/', core_views.season_two_roadmap_page, name='season2-roadmap'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
