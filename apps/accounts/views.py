"""Views for the accounts app (Unit VI: users, login/logout, sessions)."""
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.artifacts.models import Artifact

from .forms import ProfileForm, SignupForm

User = get_user_model()


def signup(request):
    if request.user.is_authenticated:
        return redirect("artifacts:home")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # log the new user in straight away
            messages.success(request, f"Welcome to HeritageArc, {user.username}!")
            return redirect("artifacts:home")  # POST -> redirect -> GET
    else:
        form = SignupForm()
    return render(request, "accounts/form.html", {
        "form": form, "title": "Create your account", "submit_label": "Sign up",
        "footer_link": ("Already registered?", "Log in", "accounts:login"),
    })


def profile(request, username):
    """Public profile page. The owner also sees their pending/rejected uploads."""
    owner = get_object_or_404(User.objects.select_related("profile"), username=username)
    is_owner = request.user == owner

    artifacts = owner.artifacts.select_related("category")
    collections = owner.collections.all()
    liked = None
    if is_owner:
        liked = owner.liked_artifacts.approved().select_related("category")
    else:
        artifacts = artifacts.approved()
        collections = collections.filter(is_private=False)

    return render(request, "accounts/profile.html", {
        "owner": owner,
        "artifacts": artifacts,
        "liked": liked,
        "collections": collections,
        "is_owner": is_owner,
    })


@login_required
def profile_edit(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user.profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("accounts:profile", username=request.user.username)
    return render(request, "accounts/form.html", {
        "form": form, "title": "Edit profile", "submit_label": "Save", "multipart": True,
    })


@login_required
def my_activity(request):
    """Shows what the session remembers: recently viewed artifacts (Unit VI sessions)."""
    ids = request.session.get("recent_artifacts", [])
    by_id = Artifact.objects.visible_to(request.user).select_related("category").in_bulk(ids)
    recent = [by_id[i] for i in ids if i in by_id]
    return render(request, "accounts/activity.html", {"recent": recent})
