"""Collections: user-curated sets of artifacts."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.artifacts.models import Artifact

from .forms import CollectionForm
from .models import Collection


def _own_collection_or_403(request, pk):
    if not str(pk).isdigit():  # e.g. a forged form value such as "abc"
        raise Http404("No such collection.")
    collection = get_object_or_404(Collection, pk=pk)
    if collection.owner_id != request.user.id:
        return collection, HttpResponseForbidden("This is not your collection.")
    return collection, None


def collection_list(request):
    visible = Q(is_private=False)
    if request.user.is_authenticated:
        visible |= Q(owner=request.user)
    collections = (Collection.objects.filter(visible).select_related("owner")
                   .annotate(item_count=Count("artifacts", distinct=True)))
    return render(request, "curation/list.html", {"collections": collections})


def collection_detail(request, pk):
    collection = get_object_or_404(Collection.objects.select_related("owner"), pk=pk)
    if not collection.can_view(request.user):
        raise Http404("No such collection.")  # do not even reveal that a private one exists
    artifacts = collection.artifacts.visible_to(request.user).select_related("category")
    return render(request, "curation/detail.html", {
        "collection": collection, "artifacts": artifacts,
        "is_owner": request.user == collection.owner,
    })


@login_required
def collection_create(request):
    form = CollectionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        collection = form.save(commit=False)
        collection.owner = request.user
        collection.save()
        messages.success(request, "Collection created. Add artifacts from their detail pages.")
        return redirect(collection)
    return render(request, "curation/form.html", {"form": form, "title": "New collection"})


@login_required
def collection_edit(request, pk):
    collection, forbidden = _own_collection_or_403(request, pk)
    if forbidden:
        return forbidden
    form = CollectionForm(request.POST or None, instance=collection)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Collection updated.")
        return redirect(collection)
    return render(request, "curation/form.html", {"form": form, "title": f"Edit: {collection.title}"})


@login_required
def collection_delete(request, pk):
    collection, forbidden = _own_collection_or_403(request, pk)
    if forbidden:
        return forbidden
    if request.method == "POST":
        collection.delete()
        messages.success(request, "Collection deleted.")
        return redirect("curation:list")
    return render(request, "curation/confirm_delete.html", {"collection": collection})


@login_required
@require_POST
def add_artifact(request):
    """The form posts both ids, so the URL stays simple: /collections/add/."""
    collection, forbidden = _own_collection_or_403(request, request.POST.get("collection"))
    if forbidden:
        return forbidden
    artifact = get_object_or_404(Artifact.objects.visible_to(request.user), pk=request.POST.get("artifact"))
    collection.artifacts.add(artifact)
    messages.success(request, f"Added to '{collection.title}'.")
    return redirect(artifact)


@login_required
@require_POST
def remove_artifact(request, pk, artifact_id):
    collection, forbidden = _own_collection_or_403(request, pk)
    if forbidden:
        return forbidden
    collection.artifacts.remove(artifact_id)
    messages.success(request, "Removed from collection.")
    return redirect(collection)
