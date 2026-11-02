"""Forms for the accounts app (Unit IV: building forms, validation)."""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from apps.artifacts.validators import validate_image_file

from .models import Profile

User = get_user_model()


class SignupForm(UserCreationForm):
    """Built-in UserCreationForm + a required, unique e-mail address."""

    email = forms.EmailField(required=True, help_text="We never share your e-mail.")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this e-mail already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    avatar = forms.ImageField(required=False, validators=[validate_image_file])

    class Meta:
        model = Profile
        fields = ("bio", "avatar")
        widgets = {"bio": forms.TextInput(attrs={"placeholder": "A line about you"})}
