"""Values available in every template."""


def site_context(request):
    theme = request.COOKIES.get("theme", "light")  # Unit VI: reading a cookie
    if theme not in ("light", "dark"):
        theme = "light"
    pending_count = 0
    user = request.user
    if user.is_authenticated and user.has_perm("artifacts.can_moderate"):
        from .models import Artifact
        pending_count = Artifact.objects.pending().count()
    return {"theme": theme, "pending_count": pending_count}
