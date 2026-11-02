from django.test import SimpleTestCase

from apps.artifacts.models import Artifact
from apps.artifacts.moderation import score_text

from .helpers import GOOD_TEXT

S = Artifact.Status


class ScoreTextTests(SimpleTestCase):
    def test_detailed_cultural_text_is_approved(self):
        result = score_text("Stone Guardian", GOOD_TEXT, "Chola era", "Tamil Nadu")
        self.assertEqual(result.decision, S.APPROVED)
        self.assertGreaterEqual(result.score, 70)

    def test_blocked_terms_are_rejected_outright(self):
        result = score_text("Free money", "Click here for a bitcoin giveaway now please", "", "")
        self.assertEqual(result.decision, S.REJECTED)
        self.assertEqual(result.score, 0)

    def test_meme_with_link_is_rejected(self):
        result = score_text("LOL MEME PIC", "lol funny pic http://spam.example", "", "")
        self.assertEqual(result.decision, S.REJECTED)

    def test_vague_text_goes_to_human_review(self):
        result = score_text("My old vase", "An old vase my grandmother gave to me when I was a child.", "", "")
        self.assertEqual(result.decision, S.PENDING)

    def test_score_is_clamped_between_0_and_100(self):
        result = score_text("AAAAAAAAAAA", "lol " * 3 + "aaaaaaaaaa http://x.y", "", "")
        self.assertTrue(0 <= result.score <= 100)

    def test_reasons_explain_the_decision(self):
        result = score_text("Stone Guardian", GOOD_TEXT, "Chola era", "Tamil Nadu")
        self.assertIn("Cultural keywords", result.reason_text)
