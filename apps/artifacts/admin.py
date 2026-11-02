"""Django Admin configuration (Unit V)."""
from django.contrib import admin
from django.utils import timezone

from .models import Artifact, Category, Comment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0


@admin.register(Artifact)
class ArtifactAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "era", "region", "status", "auto_score", "submitted_by", "created_at")
    list_filter = ("status", "category", "region")
    search_fields = ("title", "description", "era", "region")
    readonly_fields = ("auto_score", "auto_reason", "auto_reviewed_at", "created_at", "updated_at")
    inlines = [CommentInline]
    actions = ["approve_selected", "reject_selected"]

    @admin.action(description="Approve selected artifacts")
    def approve_selected(self, request, queryset):
        count = queryset.update(
            status=Artifact.Status.APPROVED, reviewed_by=request.user, reviewed_at=timezone.now()
        )
        self.message_user(request, f"{count} artifact(s) approved.")

    @admin.action(description="Reject selected artifacts")
    def reject_selected(self, request, queryset):
        count = queryset.update(
            status=Artifact.Status.REJECTED, reviewed_by=request.user, reviewed_at=timezone.now()
        )
        self.message_user(request, f"{count} artifact(s) rejected.")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "artifact", "created_at")
    search_fields = ("text", "author__username")
