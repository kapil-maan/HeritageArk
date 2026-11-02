"""
Load demo data:  python manage.py seed_demo

Creates users, artifacts (with generated images), comments, likes and a collection,
so the site looks alive right after cloning. Safe to run more than once.
"""
import io
import random

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw

from apps.artifacts.models import Artifact, Category, Comment
from apps.curation.models import Collection

User = get_user_model()
S = Artifact.Status

ARTIFACTS = [
    ("Bronze Nataraja Statue", "Sculpture", "Chola Dynasty, 11th century", "Tamil Nadu, India",
     "A cast bronze sculpture of Shiva as the lord of dance, made with the traditional lost-wax craft. "
     "The flowing arms and the ring of flames symbolise the cycle of creation and destruction in ancient temple ritual.", (176, 112, 52)),
    ("Banarasi Silk Brocade", "Textile", "Mughal Era, 17th century", "Uttar Pradesh, India",
     "A heritage brocade woven with real gold thread on silk. Mughal court artisans blended Persian floral motifs with "
     "Indian weaving, and the technique is still practised by traditional weaver families today.", (140, 40, 90)),
    ("Illuminated Quran Folio", "Manuscript", "Timurid Period, 15th century", "Herat, Afghanistan",
     "A page from a medieval manuscript with gold illumination and delicate calligraphy. The border carries inscriptions "
     "in lapis blue, and the paper was burnished by hand to a smooth historic finish.", (30, 70, 120)),
    ("Hoysala Temple Pillar", "Architecture", "Hoysala Empire, 12th century", "Karnataka, India",
     "A lathe-turned soapstone pillar from a Hoysala temple, carved with astonishing detail. The polished surface is "
     "a signature of the dynasty's masons, whose sculpture and art made the region famous.", (95, 100, 80)),
    ("Blue Pottery Vase", "Pottery", "Mughal Era, 17th century", "Jaipur, Rajasthan",
     "A traditional blue pottery vase made from quartz and glaze instead of clay. The craft came to Jaipur from Persia "
     "and the cobalt floral pattern is painted entirely by hand.", (40, 90, 160)),
    ("Pahari Miniature Painting", "Painting", "Kangra School, 18th century", "Himachal Pradesh, India",
     "A delicate miniature depicting a folk romance in a hill landscape. Painted with mineral pigments on handmade paper, "
     "it shows the lyrical heritage of the Kangra court artists.", (60, 120, 80)),
    ("Kundan Necklace", "Jewellery", "Rajput Period, 16th century", "Rajasthan, India",
     "A traditional kundan necklace with uncut gems set in gold foil. Rajput royal families commissioned such pieces "
     "and the craft of setting is passed down through generations of artisans.", (170, 130, 40)),
    ("Damascus Steel Sword", "Weapons", "Medieval, 14th century", "Syria",
     "A historic curved sword forged from crucible steel with the typical watered pattern. Famous across medieval trade "
     "routes, its smithing technique became a lost craft that museums still study.", (90, 90, 100)),
    ("Warli Tribal Mural", "Painting", "Traditional, 20th century", "Maharashtra, India",
     "A folk wall painting in white on a mud-red ground, depicting harvest rituals with simple geometric figures. "
     "Warli art is a living tribal tradition kept alive by village women.", (150, 70, 50)),
    ("Terracotta Horse of Bankura", "Sculpture", "Traditional, 19th century", "West Bengal, India",
     "A tall hollow terracotta horse, a folk ritual offering made by village potters. The stylised neck and ears are "
     "instantly recognisable as a heritage craft of Bengal.", (160, 80, 40)),
]
PENDING = ("Grandmother's Old Brass Lamp", "Jewellery", "Unknown", "Kerala, India",
           "A brass lamp that my grandmother used every evening at home for many years.", (150, 120, 30))
REJECTED = ("LOL funny meme pic", "Painting", "Today", "Internet",
            "lol this is a funny meme lmao check http://spam.example", (200, 40, 40))


def make_image(label, color, seed):
    """Draw a simple patterned placeholder so the demo needs no downloaded photos."""
    rng = random.Random(seed)
    w, h = 800, 600
    img = Image.new("RGB", (w, h), color)
    draw = ImageDraw.Draw(img)
    for y in range(h):  # vertical gradient
        shade = int(90 * y / h)
        draw.line([(0, y), (w, y)], fill=tuple(max(0, c - shade) for c in color))
    for _ in range(14):  # overlapping translucent-looking circles
        r = rng.randint(40, 190)
        x, y = rng.randint(0, w), rng.randint(0, h)
        tint = tuple(min(255, c + rng.randint(15, 70)) for c in color)
        draw.ellipse([x - r, y - r, x + r, y + r], outline=tint, width=3)
    draw.rectangle([30, 30, w - 30, h - 30], outline=(255, 244, 220), width=4)
    draw.text((60, h - 90), label[:40], fill=(255, 244, 220))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return ContentFile(buffer.getvalue())


class Command(BaseCommand):
    help = "Create demo users, artifacts, comments and a collection."

    def handle(self, *args, **options):
        if Artifact.objects.exists():
            self.stdout.write(self.style.WARNING("Artifacts already exist, nothing to do."))
            return

        password = "heritage123"
        admin, _ = User.objects.get_or_create(username="admin", defaults={
            "email": "admin@example.com", "is_staff": True, "is_superuser": True})
        moderator, _ = User.objects.get_or_create(username="moderator", defaults={"email": "mod@example.com"})
        moderator.groups.add(Group.objects.get(name="Moderators"))
        priya, _ = User.objects.get_or_create(username="priya", defaults={"email": "priya@example.com"})
        arjun, _ = User.objects.get_or_create(username="arjun", defaults={"email": "arjun@example.com"})
        for user in (admin, moderator, priya, arjun):
            user.set_password(password)
            user.save()
        priya.profile.bio = "Textile historian and weekend museum wanderer."
        priya.profile.save()

        users = [priya, arjun]
        created = []
        for i, (title, cat, era, region, desc, color) in enumerate(ARTIFACTS):
            artifact = Artifact(
                title=title, description=desc, category=Category.objects.get(name=cat), era=era, region=region,
                status=S.APPROVED, submitted_by=users[i % 2], reviewed_by=moderator,
                reviewed_at=timezone.now(), auto_score=80, auto_reason="Seeded demo data",
            )
            artifact.image.save(f"seed-{i}.jpg", make_image(title, color, i), save=False)
            artifact.save()
            created.append(artifact)

        title, cat, era, region, desc, color = PENDING
        pending = Artifact(title=title, description=desc, category=Category.objects.get(name=cat), era=era,
                           region=region, status=S.PENDING, submitted_by=arjun, auto_score=56,
                           auto_reason="Short description; no cultural keywords found")
        pending.image.save("seed-pending.jpg", make_image(title, color, 98), save=False)
        pending.save()

        title, cat, era, region, desc, color = REJECTED
        rejected = Artifact(title=title, description=desc, category=Category.objects.get(name=cat), era=era,
                            region=region, status=S.REJECTED, submitted_by=arjun, auto_score=0,
                            review_note="Rejected automatically: looks like a meme with links")
        rejected.image.save("seed-rejected.jpg", make_image(title, color, 99), save=False)
        rejected.save()

        for artifact in created:
            artifact.likes.add(*random.sample([priya, arjun, moderator, admin], k=random.randint(0, 4)))
        Comment.objects.create(artifact=created[0], author=arjun, text="The detail on the flames is stunning.")
        Comment.objects.create(artifact=created[0], author=moderator, text="Verified against the museum catalogue.")
        Comment.objects.create(artifact=created[1], author=priya, text="My family still weaves this pattern.")

        collection = Collection.objects.create(
            title="Masterpieces of South India", owner=priya,
            description="Temple art and craft traditions from the south.")
        collection.artifacts.add(created[0], created[3])
        Collection.objects.create(title="Draft ideas", owner=priya, is_private=True)

        self.stdout.write(self.style.SUCCESS(
            f"Demo data ready. Log in as admin / moderator / priya / arjun with password '{password}'."))
