from django.urls import path
from . import views

urlpatterns = [
    path("collections/", views.list_collections, name="list_collections"),
    path("collections/query/", views.query_collection, name="query_collection"),
    path("collections/insert/", views.insert_document, name="insert_document"),
    path("collections/update/", views.update_document, name="update_document"),
    path("collections/delete/", views.delete_document, name="delete_document"),
    path("collections/export/", views.export_collection, name="export_collection"),
    path("collections/<str:collection>/info/", views.get_collection_info, name="get_collection_info"),
    path("health/", views.health, name="health"),
]