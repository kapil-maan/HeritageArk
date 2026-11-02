"""Shared helpers for tests."""
import io
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from apps.artifacts.models import Artifact, Category

User = get_user_model()

GOOD_TEXT = (
    "A carved sandstone sculpture from an ancient temple of the medieval dynasty, "
    "showing traditional craft and ritual scenes from the twelfth century."
)

_TMP_MEDIA = tempfile.mkdtemp(prefix="heritagearc-test-")


def make_image(name="test.png", size=(40, 30), color=(180, 83, 42)):
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=_TMP_MEDIA)
class BaseTestCase(TestCase):
    """Creates users, a category and offers a quick artifact factory."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(_TMP_MEDIA, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        cls.password = "Str0ng-pass-123"
        cls.alice = User.objects.create_user("alice", "alice@example.com", cls.password)
        cls.bob = User.objects.create_user("bob", "bob@example.com", cls.password)
        cls.moderator = User.objects.create_user("mod", "mod@example.com", cls.password)
        cls.moderator.groups.add(Group.objects.get(name="Moderators"))
        cls.category = Category.objects.get(name="Sculpture")

    def make_artifact(self, owner=None, status=Artifact.Status.APPROVED, **extra):
        data = dict(
            title="Stone Guardian", description=GOOD_TEXT, image=make_image(), category=self.category,
            era="Chola era", region="Tamil Nadu", status=status, submitted_by=owner or self.alice,
        )
        data.update(extra)
        return Artifact.objects.create(**data)

    def login(self, user):
        self.client.login(username=user.username, password=self.password)
