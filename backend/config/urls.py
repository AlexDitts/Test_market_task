from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import include, path

from apps.credentials.utils import set_email_credentials, set_smsru_credentials
from config.routers import router
from config.yasg import schema_view


def page_not_found_view(request: WSGIRequest, exception: Exception) -> HttpResponse:
    return render(request, "404.html", status=404)


urlpatterns = [
    path("admin/", admin.site.urls, name="admin"),
    path(
        "documentation/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-documentation-ui",
    ),
    path("api/", include(router.urls)),
    path('ckeditor/', include('ckeditor_uploader.urls')),
]
urlpatterns += static(prefix=settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
handler404 = page_not_found_view

set_smsru_credentials()
set_email_credentials()
