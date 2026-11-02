"""Models for the artifacts app (Unit V: models, foreign keys, ORM)."""
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Category(models.Model):
    """A kind of artifact (Sculpture, Textile, Manuscript...). One category -> many artifacts."""

    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ArtifactQuerySet(models.QuerySet):
    """Reusable ORM filters so views stay short."""

    def approved(self):
        return self.filter(status=Artifact.Status.APPROVED)

    def pending(self):
        return self.filter(status=Artifact.Status.PENDING)

    def visible_to(self, user):
        """Approved artifacts for everyone, plus the user's own submissions."""
        if user.is_authenticated:
            return self.filter(
                models.Q(status=Artifact.Status.APPROVED) | models.Q(submitted_by=user)
            )
        return self.approved()


class Artifact(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    # Fields that matter for moderation: editing any of them forces a new review.
    MODERATED_FIELDS = ("title", "description", "image", "category", "era", "region")

    title = models.CharField(max_length=150)
    description = models.TextField()
    image = models.ImageField(upload_to="artifacts/%Y/%m/")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="artifacts")
    era = models.CharField(max_length=80, help_text="e.g. Mughal Era, 12th century")
    region = models.CharField(max_length=80, help_text="e.g. Rajasthan, India")

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    review_note = models.TextField(blank=True, help_text="Reason shown to the contributor")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="reviewed_artifacts",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Result of the automatic screening (see moderation.py)
    auto_score = models.PositiveSmallIntegerField(null=True, blank=True)
    auto_reason = models.TextField(blank=True)
    auto_reviewed_at = models.DateTimeField(null=True, blank=True)

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="artifacts"
    )
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="liked_artifacts", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ArtifactQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        permissions = [("can_moderate", "Can approve or reject artifacts")]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("artifacts:detail", kwargs={"pk": self.pk})

    @property
    def is_approved(self):
        return self.status == self.Status.APPROVED

    def mark_reviewed(self, status, note="", reviewer=None):
        self.status = status
        self.review_note = note
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save(update_fields=["status", "review_note", "reviewed_by", "reviewed_at", "updated_at"])


class Comment(models.Model):
    artifact = models.ForeignKey(Artifact, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author} on {self.artifact}: {self.text[:30]}"
