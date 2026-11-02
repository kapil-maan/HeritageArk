"""Data migration: create the 'Moderators' group and starter categories."""
from django.db import migrations

CATEGORIES = ["Sculpture", "Textile", "Manuscript", "Architecture", "Pottery", "Painting", "Jewellery", "Weapons"]


def create_defaults(apps, schema_editor):
    Category = apps.get_model("artifacts", "Category")
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    for name in CATEGORIES:
        Category.objects.get_or_create(name=name, defaults={"slug": name.lower()})

    group, _ = Group.objects.get_or_create(name="Moderators")
    # Permissions are normally created after migrate, so create it here ourselves.
    ContentType = apps.get_model("contenttypes", "ContentType")
    ct, _ = ContentType.objects.get_or_create(app_label="artifacts", model="artifact")
    perm, _ = Permission.objects.get_or_create(
        codename="can_moderate", content_type=ct,
        defaults={"name": "Can approve or reject artifacts"},
    )
    group.permissions.add(perm)


def remove_defaults(apps, schema_editor):
    apps.get_model("auth", "Group").objects.filter(name="Moderators").delete()
    apps.get_model("artifacts", "Category").objects.filter(name__in=CATEGORIES).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("artifacts", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]
    operations = [migrations.RunPython(create_defaults, remove_defaults)]
