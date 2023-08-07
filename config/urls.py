
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authtoken.views import obtain_auth_token
from django.conf import settings
from apps.users.views import LoginAPIView

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),


    # DRF URL
    path("api/", include("apps.users.urls", namespace="users")),
    path("api/", include("apps.tracking.urls", namespace="track")),

    # DRF auth token
    path('auth/', include('djoser.urls.authtoken')),
    path('auth/', include('djoser.urls.jwt')),
    path('auth/', include('djoser.urls')),
    # path('auth/login/', LoginAPIView.as_view(), name='login'),
    
    path("auth-token/", obtain_auth_token),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs")
]
