from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse

from apps.artifacts.models import Artifact
from apps.artifacts.tests.helpers import BaseTestCase

User = get_user_model()


class SignupTests(BaseTestCase):
    def signup(self, **overrides):
        data = {"username": "newbie", "email": "newbie@example.com",
                "password1": "Fresh-pass-987", "password2": "Fresh-pass-987"}
        data.update(overrides)
        return self.client.post(reverse("accounts:signup"), data)

    def test_signup_creates_user_profile_and_logs_in(self):
        response = self.signup()
        self.assertRedirects(response, reverse("artifacts:home"))
        user = User.objects.get(username="newbie")
        self.assertTrue(hasattr(user, "profile"))  # created by the post_save signal
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_duplicate_email_rejected_case_insensitively(self):
        response = self.signup(email="ALICE@example.com")
        self.assertIn("email", response.context["form"].errors)
        self.assertFalse(User.objects.filter(username="newbie").exists())

    def test_password_mismatch_rejected(self):
        response = self.signup(password2="different")
        self.assertIn("password2", response.context["form"].errors)

    def test_weak_password_rejected(self):
        response = self.signup(password1="12345678", password2="12345678")
        self.assertIn("password2", response.context["form"].errors)


class LoginLogoutTests(BaseTestCase):
    def test_login_then_logout(self):
        response = self.client.post(reverse("accounts:login"), {"username": "alice", "password": self.password})
        self.assertRedirects(response, reverse("artifacts:home"))
        self.client.post(reverse("accounts:logout"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_wrong_password(self):
        response = self.client.post(reverse("accounts:login"), {"username": "alice", "password": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_next_parameter_is_honoured(self):
        response = self.client.post(
            reverse("accounts:login") + "?next=/submit/", {"username": "alice", "password": self.password, "next": "/submit/"})
        self.assertRedirects(response, "/submit/")

    def test_logout_rejects_get(self):
        self.login(self.alice)
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)


class ProfileTests(BaseTestCase):
    def test_public_profile_hides_pending_work(self):
        self.make_artifact(title="Live One")
        self.make_artifact(title="Hidden One", status=Artifact.Status.PENDING)
        response = self.client.get(reverse("accounts:profile", args=["alice"]))
        self.assertContains(response, "Live One")
        self.assertNotContains(response, "Hidden One")

    def test_owner_sees_own_pending_work(self):
        self.make_artifact(title="Hidden One", status=Artifact.Status.PENDING)
        self.login(self.alice)
        self.assertContains(self.client.get(reverse("accounts:profile", args=["alice"])), "Hidden One")

    def test_unknown_user_404(self):
        self.assertEqual(self.client.get(reverse("accounts:profile", args=["ghost"])).status_code, 404)

    def test_settings_requires_login_and_saves_bio(self):
        self.assertEqual(self.client.get(reverse("accounts:settings")).status_code, 302)
        self.login(self.alice)
        self.client.post(reverse("accounts:settings"), {"bio": "Collector of coins"})
        self.alice.profile.refresh_from_db()
        self.assertEqual(self.alice.profile.bio, "Collector of coins")


class PasswordResetTests(BaseTestCase):
    def test_reset_email_is_sent_with_a_link(self):
        self.client.post(reverse("accounts:password_reset"), {"email": "alice@example.com"})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/accounts/reset/", mail.outbox[0].body)

    def test_unknown_email_sends_nothing_but_looks_identical(self):
        response = self.client.post(reverse("accounts:password_reset"), {"email": "nobody@example.com"})
        self.assertRedirects(response, reverse("accounts:reset_sent"))
        self.assertEqual(len(mail.outbox), 0)
