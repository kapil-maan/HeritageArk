from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import Profile

User = get_user_model()


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False


class UserWithProfileAdmin(UserAdmin):
    """Show the profile on the same page as the user."""

    inlines = [ProfileInline]


admin.site.unregister(User)
admin.site.register(User, UserWithProfileAdmin)
