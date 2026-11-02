from django.contrib import admin

from .models import Collection


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "is_private", "updated_at")
    list_filter = ("is_private",)
    search_fields = ("title", "owner__username")
    filter_horizontal = ("artifacts",)
