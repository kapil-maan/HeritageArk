"""
Automatic screening of new submissions.

The original HeritageArc app asked an AI model to judge each submission and
used confidence thresholds to decide the outcome. Here the same *workflow* is
kept, but the judge is a transparent, rule-based scorer, so every decision can
be explained line by line (and it needs no API key).

    score >= 70  -> approved automatically
    score <= 20  -> rejected automatically
    otherwise    -> pending, a human moderator decides
"""
import re
from dataclasses import dataclass, field

from django.utils import timezone

from .models import Artifact

APPROVE_AT = 70
REJECT_AT = 20

BLOCKED_TERMS = {"porn", "nsfw", "casino", "viagra", "bitcoin giveaway", "free money"}
MEME_TERMS = {"meme", "lol", "lmao", "shitpost", "funny pic"}
CULTURAL_TERMS = {
    "heritage", "ancient", "temple", "manuscript", "sculpture", "dynasty", "textile",
    "pottery", "traditional", "empire", "medieval", "ritual", "craft", "inscription",
    "fort", "palace", "museum", "century", "historic", "carved", "folk", "art",
}
URL_RE = re.compile(r"(https?://|www\.)", re.IGNORECASE)
REPEAT_RE = re.compile(r"(.)\1{5,}")


@dataclass
class ScreeningResult:
    score: int
    decision: str
    reasons: list = field(default_factory=list)

    @property
    def reason_text(self):
        return "; ".join(self.reasons)


def score_text(title, description, era="", region=""):
    """Return a ScreeningResult for the given text. Pure function -> easy to test."""
    text = f"{title} {description}".lower()
    score = 50
    reasons = []

    if any(term in text for term in BLOCKED_TERMS):
        return ScreeningResult(0, Artifact.Status.REJECTED, ["Contains blocked or spam terms"])

    if any(term in text for term in MEME_TERMS):
        score -= 30
        reasons.append("Looks like a meme or joke post (-30)")

    if URL_RE.search(description):
        score -= 25
        reasons.append("Description contains links (-25)")

    if REPEAT_RE.search(text):
        score -= 15
        reasons.append("Repeated characters look like spam (-15)")

    letters = [c for c in title if c.isalpha()]
    if len(letters) > 6 and all(c.isupper() for c in letters):
        score -= 10
        reasons.append("Title is all capitals (-10)")

    words = description.split()
    if len(words) >= 25:
        score += 20
        reasons.append("Detailed description (+20)")
    elif len(words) < 8:
        score -= 15
        reasons.append("Description is very short (-15)")

    hits = sorted(term for term in CULTURAL_TERMS if term in text)
    if hits:
        bonus = min(len(hits) * 8, 24)
        score += bonus
        reasons.append(f"Cultural keywords: {', '.join(hits[:4])} (+{bonus})")
    else:
        reasons.append("No cultural keywords found")

    if era.strip() and region.strip():
        score += 6
        reasons.append("Era and region provided (+6)")

    score = max(0, min(100, score))
    if score >= APPROVE_AT:
        decision = Artifact.Status.APPROVED
    elif score <= REJECT_AT:
        decision = Artifact.Status.REJECTED
    else:
        decision = Artifact.Status.PENDING
    return ScreeningResult(score, decision, reasons)


def screen_artifact(artifact):
    """Screen an artifact, store the outcome on it, and return the result."""
    result = score_text(artifact.title, artifact.description, artifact.era, artifact.region)
    artifact.auto_score = result.score
    artifact.auto_reason = result.reason_text
    artifact.auto_reviewed_at = timezone.now()
    artifact.status = result.decision
    artifact.reviewed_by = None
    artifact.reviewed_at = None
    artifact.review_note = (
        "Rejected automatically: " + result.reason_text
        if result.decision == Artifact.Status.REJECTED else ""
    )
    artifact.save()
    return result
