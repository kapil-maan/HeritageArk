from django.urls import reverse

from apps.artifacts.models import Artifact
from apps.artifacts.tests.helpers import BaseTestCase

from .models import Collection


class CollectionTests(BaseTestCase):
    def test_create_requires_login(self):
        self.assertEqual(self.client.get(reverse("curation:create")).status_code, 302)

    def test_create_sets_owner(self):
        self.login(self.alice)
        self.client.post(reverse("curation:create"), {"title": "Temples", "description": "Stone and prayer"})
        self.assertEqual(Collection.objects.get().owner, self.alice)

    def test_private_collection_is_hidden_from_others(self):
        collection = Collection.objects.create(title="Secret", owner=self.alice, is_private=True)
        self.assertEqual(self.client.get(collection.get_absolute_url()).status_code, 404)
        self.login(self.bob)
        self.assertEqual(self.client.get(collection.get_absolute_url()).status_code, 404)
        self.assertNotContains(self.client.get(reverse("curation:list")), "Secret")
        self.login(self.alice)
        self.assertEqual(self.client.get(collection.get_absolute_url()).status_code, 200)

    def test_add_and_remove_artifact(self):
        artifact = self.make_artifact()
        collection = Collection.objects.create(title="Mine", owner=self.bob)
        self.login(self.bob)
        self.client.post(reverse("curation:add"), {"collection": collection.pk, "artifact": artifact.pk})
        self.assertIn(artifact, collection.artifacts.all())
        self.client.post(reverse("curation:remove", args=[collection.pk, artifact.pk]))
        self.assertEqual(collection.artifacts.count(), 0)

    def test_cannot_modify_someone_elses_collection(self):
        artifact = self.make_artifact()
        collection = Collection.objects.create(title="Alice only", owner=self.alice)
        self.login(self.bob)
        response = self.client.post(reverse("curation:add"), {"collection": collection.pk, "artifact": artifact.pk})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.post(reverse("curation:delete", args=[collection.pk])).status_code, 403)

    def test_cannot_add_unapproved_artifact_of_another_user(self):
        hidden = self.make_artifact(status=Artifact.Status.PENDING)  # alice's
        collection = Collection.objects.create(title="Bob's", owner=self.bob)
        self.login(self.bob)
        response = self.client.post(reverse("curation:add"), {"collection": collection.pk, "artifact": hidden.pk})
        self.assertEqual(response.status_code, 404)

    def test_deleting_collection_keeps_artifacts(self):
        artifact = self.make_artifact()
        collection = Collection.objects.create(title="Temp", owner=self.alice)
        collection.artifacts.add(artifact)
        self.login(self.alice)
        self.client.post(reverse("curation:delete", args=[collection.pk]))
        self.assertTrue(Artifact.objects.filter(pk=artifact.pk).exists())
