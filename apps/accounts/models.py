from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Extra data for a user, one-to-one with the built-in User model."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    bio = models.CharField(max_length=240, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
