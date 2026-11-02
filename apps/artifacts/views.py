"""Views for the artifacts app (Units II, III, IV, VI)."""
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.curation.models import Collection

from .forms import ArtifactForm, CommentForm, ExploreForm, ModerationForm
from .models import Artifact, Comment
from .moderation import screen_artifact

User = get_user_model()
PAGE_SIZE = 12
RECENT_LIMIT = 8


def can_manage(user, artifact):
    """Owners and moderators may edit or delete an artifact."""
    return user.is_authenticated and (
        artifact.submitted_by_id == user.id or user.has_perm("artifacts.can_moderate")
    )


def get_visible_artifact(request, pk):
    """Approved artifacts are public; others only for their owner or a moderator."""
    artifact = get_object_or_404(
        Artifact.objects.select_related("category", "submitted_by", "reviewed_by"), pk=pk
    )
    if not artifact.is_approved and not can_manage(request.user, artifact):
        raise Http404("No such artifact.")
    return artifact


# ---------------------------------------------------------------- public pages

def home(request):
    approved = Artifact.objects.approved().select_related("category")
    context = {
        "latest": approved[:8],
        "popular": approved.annotate(n=Count("likes")).order_by("-n", "-created_at")[:4],
        "stats": {
            "artifacts": approved.count(),
            "contributors": User.objects.filter(artifacts__status=Artifact.Status.APPROVED).distinct().count(),
            "collections": Collection.objects.filter(is_private=False).count(),
        },
    }
    return render(request, "artifacts/home.html", context)


def explore(request):
    form = ExploreForm(request.GET)
    artifacts = Artifact.objects.approved().select_related("category")

    if form.is_valid():
        q = form.cleaned_data["q"].strip()
        if q:
            artifacts = artifacts.filter(
                Q(title__icontains=q) | Q(description__icontains=q) | Q(era__icontains=q) | Q(region__icontains=q)
            )
        if form.cleaned_data["category"]:
            artifacts = artifacts.filter(category=form.cleaned_data["category"])
        sort = form.cleaned_data["sort"]
        if sort == "old":
            artifacts = artifacts.order_by("created_at")
        elif sort == "popular":
            artifacts = artifacts.annotate(n=Count("likes")).order_by("-n", "-created_at")

    page_obj = Paginator(artifacts, PAGE_SIZE).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    query_string = params.urlencode()
    return render(request, "artifacts/explore.html", {
        "form": form, "page_obj": page_obj,
        "query_string": f"{query_string}&" if query_string else "",
    })


def archive_year(request, year):
    """Reached through a regular expression URL: /archive/2026/ (Unit II)."""
    artifacts = Artifact.objects.approved().select_related("category").filter(created_at__year=year)
    return render(request, "artifacts/archive.html", {"year": year, "artifacts": artifacts})


def detail(request, pk):
    artifact = get_visible_artifact(request, pk)

    # Unit VI: remember recently viewed artifacts in the session (most recent first).
    recent = [i for i in request.session.get("recent_artifacts", []) if i != artifact.pk]
    request.session["recent_artifacts"] = [artifact.pk] + recent[:RECENT_LIMIT - 1]

    context = {
        "artifact": artifact,
        "comments": artifact.comments.select_related("author"),
        "comment_form": CommentForm(),
        "liked": request.user.is_authenticated and artifact.likes.filter(pk=request.user.pk).exists(),
        "can_manage": can_manage(request.user, artifact),
        "my_collections": (
            Collection.objects.filter(owner=request.user).exclude(artifacts=artifact)
            if request.user.is_authenticated else []
        ),
    }
    return render(request, "artifacts/detail.html", context)


# ------------------------------------------------------------- contributor pages

@login_required
def create(request):
    form = ArtifactForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        artifact = form.save(commit=False)
        artifact.submitted_by = request.user
        artifact.save()
        result = screen_artifact(artifact)
        messages.add_message(
            request,
            messages.SUCCESS if artifact.is_approved else messages.WARNING,
            {
                Artifact.Status.APPROVED: "Your artifact passed screening and is now live.",
                Artifact.Status.PENDING: "Submitted! A moderator will review it shortly.",
                Artifact.Status.REJECTED: f"Sorry, it was rejected automatically: {result.reason_text}",
            }[artifact.status],
        )
        return redirect(artifact)  # Post/Redirect/Get, avoids duplicate submissions on refresh
    return render(request, "artifacts/form.html", {"form": form, "title": "Submit an artifact"})


@login_required
def edit(request, pk):
    artifact = get_object_or_404(Artifact, pk=pk)
    if not can_manage(request.user, artifact):
        return HttpResponseForbidden("You can only edit your own artifacts.")

    form = ArtifactForm(request.POST or None, request.FILES or None, instance=artifact)
    if request.method == "POST" and form.is_valid():
        # Any change to a moderated field invalidates the earlier decision.
        needs_review = any(f in form.changed_data for f in Artifact.MODERATED_FIELDS)
        artifact = form.save()
        if needs_review:
            screen_artifact(artifact)
            messages.warning(request, f"Saved. Because content changed it was re-screened: {artifact.get_status_display()}.")
        else:
            messages.success(request, "Saved.")
        return redirect(artifact)
    return render(request, "artifacts/form.html", {"form": form, "title": f"Edit: {artifact.title}"})


@login_required
def delete(request, pk):
    artifact = get_object_or_404(Artifact, pk=pk)
    if not can_manage(request.user, artifact):
        return HttpResponseForbidden("You can only delete your own artifacts.")
    if request.method == "POST":
        artifact.image.delete(save=False)
        artifact.delete()
        messages.success(request, "Artifact deleted.")
        return redirect("artifacts:home")
    return render(request, "artifacts/confirm_delete.html", {"artifact": artifact})


@login_required
@require_POST
def toggle_like(request, pk):
    artifact = get_visible_artifact(request, pk)
    if artifact.likes.filter(pk=request.user.pk).exists():
        artifact.likes.remove(request.user)
    else:
        artifact.likes.add(request.user)
    return redirect(artifact)


@login_required
@require_POST
def add_comment(request, pk):
    artifact = get_visible_artifact(request, pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        Comment.objects.create(artifact=artifact, author=request.user, text=form.cleaned_data["text"])
        messages.success(request, "Comment added.")
    else:
        messages.error(request, "; ".join(form.errors.get("text", ["Invalid comment."])))
    return redirect(artifact)


@login_required
@require_POST
def delete_comment(request, pk, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, artifact_id=pk)
    if comment.author_id != request.user.id and not request.user.has_perm("artifacts.can_moderate"):
        return HttpResponseForbidden("Not your comment.")
    comment.delete()
    messages.success(request, "Comment removed.")
    return redirect("artifacts:detail", pk=pk)


# ------------------------------------------------------------------ moderation

@permission_required("artifacts.can_moderate", raise_exception=True)
def moderation_queue(request):
    pending = Artifact.objects.pending().select_related("category", "submitted_by").order_by("created_at")
    recent = (Artifact.objects.exclude(status=Artifact.Status.PENDING)
              .select_related("category", "reviewed_by").order_by("-updated_at")[:10])
    return render(request, "artifacts/moderation.html", {"pending": pending, "recent": recent})


@permission_required("artifacts.can_moderate", raise_exception=True)
@require_POST
def moderate(request, pk):
    artifact = get_object_or_404(Artifact, pk=pk)
    form = ModerationForm(request.POST)
    if form.is_valid():
        approve = form.cleaned_data["decision"] == "approve"
        artifact.mark_reviewed(
            Artifact.Status.APPROVED if approve else Artifact.Status.REJECTED,
            note=form.cleaned_data["note"].strip(),
            reviewer=request.user,
        )
        messages.success(request, f"'{artifact.title}' {'approved' if approve else 'rejected'}.")
    else:
        messages.error(request, "; ".join(e for errs in form.errors.values() for e in errs))
    return redirect("artifacts:moderation")


# ---------------------------------------------------------------- cookie / theme

@require_POST
def set_theme(request):
    """Unit VI: write a cookie. The theme survives log-out because it is a cookie, not session data."""
    theme = request.POST.get("theme", "light")
    if theme not in ("light", "dark"):
        theme = "light"
    target = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
        target = "/"
    response = redirect(target)
    response.set_cookie("theme", theme, max_age=60 * 60 * 24 * 365, samesite="Lax")
    return response


# --------------------------------------------------------------- error handlers

def error_404(request, exception):
    return render(request, "404.html", status=404)


def error_403(request, exception):
    return render(request, "403.html", status=403)


def error_500(request):
    return render(request, "500.html", status=500)
