"""URL patterns for artifacts (Unit II: mapping URLs, parameters, regular expressions)."""
from django.urls import path, re_path

from . import views

app_name = "artifacts"

urlpatterns = [
    path("", views.home, name="home"),
    path("explore/", views.explore, name="explore"),
    path("submit/", views.create, name="create"),
    path("theme/", views.set_theme, name="set_theme"),

    # Regular-expression route: exactly four digits for the year.
    re_path(r"^archive/(?P<year>[0-9]{4})/$", views.archive_year, name="archive"),

    # <int:pk> is a path converter: it captures the id and passes it to the view.
    path("artifacts/<int:pk>/", views.detail, name="detail"),
    path("artifacts/<int:pk>/edit/", views.edit, name="edit"),
    path("artifacts/<int:pk>/delete/", views.delete, name="delete"),
    path("artifacts/<int:pk>/like/", views.toggle_like, name="like"),
    path("artifacts/<int:pk>/comments/", views.add_comment, name="comment"),
    path("artifacts/<int:pk>/comments/<int:comment_id>/delete/", views.delete_comment, name="comment_delete"),

    path("moderation/", views.moderation_queue, name="moderation"),
    path("moderation/<int:pk>/decide/", views.moderate, name="moderate"),
]
