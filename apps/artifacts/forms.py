"""Forms for the artifacts app (Unit IV)."""
from django import forms

from .models import Artifact, Category, Comment
from .validators import validate_image_file


class ArtifactForm(forms.ModelForm):
    """Create / edit an artifact. A ModelForm builds fields and validation from the model."""

    image = forms.ImageField(validators=[validate_image_file], help_text="JPEG, PNG or WebP, up to 5 MB.")

    class Meta:
        model = Artifact
        fields = ("title", "description", "category", "era", "region", "image")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
            "era": forms.TextInput(attrs={"placeholder": "Mughal Era, 12th century..."}),
            "region": forms.TextInput(attrs={"placeholder": "Rajasthan, India"}),
        }

    # Field-level validation: clean_<fieldname>()
    def clean_title(self):
        title = " ".join(self.cleaned_data["title"].split())
        if len(title) < 4:
            raise forms.ValidationError("Please give the artifact a meaningful title (4+ characters).")
        return title

    def clean_description(self):
        description = self.cleaned_data["description"].strip()
        if len(description) < 30:
            raise forms.ValidationError("Describe the artifact in at least 30 characters.")
        return description


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
        labels = {"text": "Add a comment"}
        widgets = {"text": forms.Textarea(attrs={"rows": 3, "maxlength": 1000})}

    def clean_text(self):
        text = self.cleaned_data["text"].strip()
        if not text:
            raise forms.ValidationError("Comment cannot be empty.")
        return text


class ExploreForm(forms.Form):
    """Search form submitted with GET, so results can be bookmarked and shared."""

    SORT_CHOICES = [("new", "Newest first"), ("old", "Oldest first"), ("popular", "Most liked")]

    q = forms.CharField(required=False, label="Search", widget=forms.TextInput(
        attrs={"type": "search", "placeholder": "Search title, era, region..."}))
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False, empty_label="All categories")
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False)


class ModerationForm(forms.Form):
    DECISIONS = [("approve", "Approve"), ("reject", "Reject")]

    decision = forms.ChoiceField(choices=DECISIONS)
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("decision") == "reject" and not (cleaned.get("note") or "").strip():
            self.add_error("note", "Please explain why this artifact is rejected.")
        return cleaned
