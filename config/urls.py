"""Root URL configuration (Unit II). Each app owns its own urls.py and is included here."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("collections/", include("apps.curation.urls")),
    path("", include("apps.artifacts.urls")),
]

# Serve uploaded images while developing (a real web server does this in production).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Unit II: custom error pages
handler403 = "apps.artifacts.views.error_403"
handler404 = "apps.artifacts.views.error_404"
handler500 = "apps.artifacts.views.error_500"
