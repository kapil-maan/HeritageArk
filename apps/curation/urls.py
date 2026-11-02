from django.urls import path

from . import views

app_name = "curation"

urlpatterns = [
    path("", views.collection_list, name="list"),
    path("add/", views.add_artifact, name="add"),
    path("new/", views.collection_create, name="create"),
    path("<int:pk>/", views.collection_detail, name="detail"),
    path("<int:pk>/edit/", views.collection_edit, name="edit"),
    path("<int:pk>/delete/", views.collection_delete, name="delete"),
    path("<int:pk>/remove/<int:artifact_id>/", views.remove_artifact, name="remove"),
]
