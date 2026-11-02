from django import forms

from .models import Collection


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ("title", "description", "is_private")
        labels = {"is_private": "Private (only visible to me)"}
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}
