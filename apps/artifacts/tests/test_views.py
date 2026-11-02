from django.urls import reverse

from apps.artifacts.models import Artifact, Comment

from .helpers import GOOD_TEXT, BaseTestCase, make_image

S = Artifact.Status


class PublicPageTests(BaseTestCase):
    def test_home_and_explore_load(self):
        self.make_artifact()
        self.assertContains(self.client.get(reverse("artifacts:home")), "Stone Guardian")
        self.assertContains(self.client.get(reverse("artifacts:explore")), "Stone Guardian")

    def test_explore_hides_unapproved_artifacts(self):
        self.make_artifact(title="Secret Pending", status=S.PENDING)
        self.assertNotContains(self.client.get(reverse("artifacts:explore")), "Secret Pending")

    def test_search_and_category_filter(self):
        self.make_artifact(title="Bronze Dancer", era="Chola")
        self.make_artifact(title="Silk Shawl", era="Mughal")
        response = self.client.get(reverse("artifacts:explore"), {"q": "mughal"})
        self.assertContains(response, "Silk Shawl")
        self.assertNotContains(response, "Bronze Dancer")

    def test_regex_archive_url(self):
        self.make_artifact()
        year = Artifact.objects.first().created_at.year
        self.assertEqual(self.client.get(f"/archive/{year}/").status_code, 200)
        self.assertEqual(self.client.get("/archive/20/").status_code, 404)  # regex needs 4 digits

    def test_missing_page_uses_custom_404(self):
        response = self.client.get("/artifacts/9999/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "gone missing", status_code=404)


class VisibilityTests(BaseTestCase):
    def test_pending_artifact_visible_only_to_owner_and_moderator(self):
        artifact = self.make_artifact(status=S.PENDING)
        url = artifact.get_absolute_url()
        self.assertEqual(self.client.get(url).status_code, 404)
        self.login(self.bob)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.login(self.alice)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.login(self.moderator)
        self.assertEqual(self.client.get(url).status_code, 200)


class SubmissionTests(BaseTestCase):
    def post_artifact(self, **overrides):
        data = {"title": "Stone Guardian", "description": GOOD_TEXT, "category": self.category.pk,
                "era": "Chola era", "region": "Tamil Nadu", "image": make_image()}
        data.update(overrides)
        return self.client.post(reverse("artifacts:create"), data)

    def test_login_required(self):
        response = self.client.get(reverse("artifacts:create"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('artifacts:create')}")

    def test_good_submission_is_auto_approved_and_redirects(self):
        self.login(self.alice)
        response = self.post_artifact()
        artifact = Artifact.objects.get()
        self.assertRedirects(response, artifact.get_absolute_url())  # Post/Redirect/Get
        self.assertEqual(artifact.status, S.APPROVED)
        self.assertEqual(artifact.submitted_by, self.alice)

    def test_vague_submission_waits_for_review(self):
        self.login(self.alice)
        self.post_artifact(title="My old vase", era="Unknown", region="Unknown",
                           description="An old vase my grandmother gave to me when I was a child.")
        self.assertEqual(Artifact.objects.get().status, S.PENDING)

    def test_short_description_is_invalid(self):
        self.login(self.alice)
        response = self.post_artifact(description="too short")
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "description", "Describe the artifact in at least 30 characters.")
        self.assertEqual(Artifact.objects.count(), 0)

    def test_non_image_upload_is_rejected(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.login(self.alice)
        response = self.post_artifact(image=SimpleUploadedFile("x.png", b"not an image", content_type="image/png"))
        self.assertEqual(Artifact.objects.count(), 0)
        self.assertIn("image", response.context["form"].errors)

    def test_post_without_csrf_token_is_forbidden(self):
        from django.test import Client
        strict = Client(enforce_csrf_checks=True)
        strict.login(username="alice", password=self.password)
        self.assertEqual(strict.post(reverse("artifacts:create"), {}).status_code, 403)


class EditDeleteTests(BaseTestCase):
    def test_only_owner_can_edit(self):
        artifact = self.make_artifact()
        self.login(self.bob)
        self.assertEqual(self.client.get(reverse("artifacts:edit", args=[artifact.pk])).status_code, 403)

    def test_editing_content_resets_review(self):
        artifact = self.make_artifact(status=S.APPROVED)
        self.login(self.alice)
        self.client.post(reverse("artifacts:edit", args=[artifact.pk]), {
            "title": "My old vase", "description": "An old vase my grandmother gave to me when I was a child.",
            "category": self.category.pk, "era": "Unknown", "region": "Unknown",
        })
        artifact.refresh_from_db()
        self.assertEqual(artifact.status, S.PENDING)
        self.assertIsNotNone(artifact.auto_reviewed_at)

    def test_owner_can_delete_after_confirmation(self):
        artifact = self.make_artifact()
        self.login(self.alice)
        url = reverse("artifacts:delete", args=[artifact.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.post(url)
        self.assertFalse(Artifact.objects.filter(pk=artifact.pk).exists())


class LikeAndCommentTests(BaseTestCase):
    def test_like_toggles(self):
        artifact = self.make_artifact()
        self.login(self.bob)
        url = reverse("artifacts:like", args=[artifact.pk])
        self.client.post(url)
        self.assertEqual(artifact.likes.count(), 1)
        self.client.post(url)
        self.assertEqual(artifact.likes.count(), 0)

    def test_like_requires_post(self):
        artifact = self.make_artifact()
        self.login(self.bob)
        self.assertEqual(self.client.get(reverse("artifacts:like", args=[artifact.pk])).status_code, 405)

    def test_comment_create_and_delete_permissions(self):
        artifact = self.make_artifact()
        self.login(self.bob)
        self.client.post(reverse("artifacts:comment", args=[artifact.pk]), {"text": "Beautiful!"})
        comment = Comment.objects.get()
        delete_url = reverse("artifacts:comment_delete", args=[artifact.pk, comment.pk])

        self.login(self.alice)  # neither author nor moderator
        self.assertEqual(self.client.post(delete_url).status_code, 403)
        self.login(self.moderator)
        self.client.post(delete_url)
        self.assertEqual(Comment.objects.count(), 0)

    def test_blank_comment_rejected(self):
        artifact = self.make_artifact()
        self.login(self.bob)
        self.client.post(reverse("artifacts:comment", args=[artifact.pk]), {"text": "   "})
        self.assertEqual(Comment.objects.count(), 0)


class ModerationQueueTests(BaseTestCase):
    def test_regular_users_get_403(self):
        self.login(self.alice)
        self.assertEqual(self.client.get(reverse("artifacts:moderation")).status_code, 403)

    def test_anonymous_users_are_sent_to_login(self):
        self.assertEqual(self.client.get(reverse("artifacts:moderation")).status_code, 302)

    def test_moderator_approves_and_rejects(self):
        a1 = self.make_artifact(status=S.PENDING)
        a2 = self.make_artifact(status=S.PENDING, title="Other")
        self.login(self.moderator)
        self.assertContains(self.client.get(reverse("artifacts:moderation")), "Stone Guardian")
        self.client.post(reverse("artifacts:moderate", args=[a1.pk]), {"decision": "approve"})
        self.client.post(reverse("artifacts:moderate", args=[a2.pk]), {"decision": "reject", "note": "Blurry photo"})
        a1.refresh_from_db(); a2.refresh_from_db()
        self.assertEqual(a1.status, S.APPROVED)
        self.assertEqual(a1.reviewed_by, self.moderator)
        self.assertEqual((a2.status, a2.review_note), (S.REJECTED, "Blurry photo"))

    def test_rejection_requires_a_note(self):
        artifact = self.make_artifact(status=S.PENDING)
        self.login(self.moderator)
        self.client.post(reverse("artifacts:moderate", args=[artifact.pk]), {"decision": "reject", "note": ""})
        artifact.refresh_from_db()
        self.assertEqual(artifact.status, S.PENDING)


class SessionAndCookieTests(BaseTestCase):
    def test_recently_viewed_is_stored_in_session(self):
        first, second = self.make_artifact(), self.make_artifact(title="Second")
        self.client.get(first.get_absolute_url())
        self.client.get(second.get_absolute_url())
        self.client.get(first.get_absolute_url())
        self.assertEqual(self.client.session["recent_artifacts"], [first.pk, second.pk])

    def test_theme_cookie_is_set_and_applied(self):
        response = self.client.post(reverse("artifacts:set_theme"), {"theme": "dark", "next": "/explore/"})
        self.assertRedirects(response, "/explore/")
        self.assertEqual(response.cookies["theme"].value, "dark")
        self.assertContains(self.client.get("/"), 'data-theme="dark"')

    def test_theme_redirect_ignores_external_urls(self):
        response = self.client.post(reverse("artifacts:set_theme"), {"theme": "dark", "next": "https://evil.example/"})
        self.assertRedirects(response, "/")

    def test_invalid_theme_falls_back_to_light(self):
        response = self.client.post(reverse("artifacts:set_theme"), {"theme": "<script>"})
        self.assertEqual(response.cookies["theme"].value, "light")
