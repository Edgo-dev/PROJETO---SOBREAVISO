"""URLs principais do projeto sobreaviso."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("chamados.urls")),
]
