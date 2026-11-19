"""Configuration des URL du projet Kalos Business."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from boutique import views as boutique_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('boutique.urls')),
    path('connexion/', boutique_views.KalosLoginView.as_view(), name='login'),
    path('deconnexion/', auth_views.LogoutView.as_view(), name='logout'),
    path('inscription/', boutique_views.register, name='register'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
