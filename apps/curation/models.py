from django.conf import settings
from django.db import models
from django.urls import reverse


class Collection(models.Model):
    """A user-curated set of artifacts (many-to-many with Artifact)."""

    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="collections")
    artifacts = models.ManyToManyField("artifacts.Artifact", related_name="collections", blank=True)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("curation:detail", kwargs={"pk": self.pk})

    def can_view(self, user):
        return not self.is_private or (user.is_authenticated and user == self.owner)
