from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # path("admin/", admin.site.urls),
    path("api/", include("mongodb_api.urls")),  # ✅ Include API routes
]