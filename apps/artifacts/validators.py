"""Reusable validators (Unit IV: data validation)."""
from django.conf import settings
from django.core.exceptions import ValidationError

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


def validate_image_file(image):
    """Reject files that are too large or not JPEG/PNG/WebP images."""
    max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
    if image.size > max_bytes:
        raise ValidationError(f"Image is too large. Maximum size is {settings.MAX_IMAGE_SIZE_MB} MB.")
    content_type = getattr(image, "content_type", None)
    if content_type and content_type not in ALLOWED_TYPES:
        raise ValidationError("Only JPEG, PNG or WebP images are allowed.")
