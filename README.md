# HeritageArc (Django edition)

A community archive for cultural heritage. People submit artifacts (sculptures, textiles, manuscripts...),
the site screens every submission automatically, moderators decide the borderline cases, and members
like, comment and group artifacts into collections.

This is a Python / Django rebuild of the original MERN-stack HeritageArc project, structured so each
part of the **INT253 Web Development in Python using Django** syllabus can be shown in working code.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate          # creates tables + the Moderators group + starter categories
python manage.py seed_demo        # optional: demo users, artifacts, comments, collections
python manage.py runserver
```

Open <http://127.0.0.1:8000>. Demo accounts (password `heritage123`): `admin` (superuser),
`moderator` (can review submissions), `priya` and `arjun` (contributors).
Django admin lives at `/admin/`. Run the tests with `python manage.py test`.

Optional settings go in a `.env` file (see `.env.example`).

## Features

| Feature | Notes |
|---|---|
| Submit artifacts | Image upload with size/type validation, category, era, region |
| Automatic screening | Rule-based score 0-100: `>=70` approved, `<=20` rejected, otherwise a human decides |
| Moderator queue | Approve / reject with a note, permission-protected, shows the screening reasons |
| Explore | GET search form, category filter, sorting, pagination |
| Likes and comments | Toggle like, comment, authors and moderators can delete |
| Collections | Public or private sets of artifacts, owner-only editing |
| Accounts | Signup, login/logout, profile + avatar, password change and reset (console e-mail) |
| Recently viewed | Stored in the **session** |
| Light / dark theme | Stored in a **cookie** |
| Custom 403 / 404 / 500 pages | Plus a regex URL: `/archive/2026/` |

**What changed from the Node version?** The external AI moderation call (Gemini) became a transparent,
rule-based scorer in [`moderation.py`](apps/artifacts/moderation.py), the workflow with approve/reject/pending thresholds
is the same, but every decision is explainable and needs no API key. OTP e-mail signup became Django's
built-in auth with password-reset links. Cloudinary uploads became Django's `ImageField` + media folder.
JWT became session cookies.

## Syllabus map (where to show each unit)

| Unit | Topic | Where in this project |
|---|---|---|
| I | Project, apps, `manage.py` | `config/` (project), `apps/accounts`, `apps/artifacts`, `apps/curation` (apps), `settings.py` |
| II | Views, URLs, params, regex, errors | [`artifacts/urls.py`](apps/artifacts/urls.py) (`<int:pk>`, `re_path` archive), [`views.py`](apps/artifacts/views.py), `handler404/403/500` in [`config/urls.py`](config/urls.py) |
| III | Templates, DTL, inheritance, debugging, testing | [`templates/base.html`](templates/base.html) + `{% extends %}`, `{% for %}`, `{% if %}`, `{% include %}`, filters; `apps/*/tests` (54 tests) |
| IV | Forms, GET/POST, CSRF, validation, PRG | [`artifacts/forms.py`](apps/artifacts/forms.py) (`ModelForm`, `clean_<field>`, GET `ExploreForm`), `{% csrf_token %}`, `return redirect(...)` after every POST |
| V | Models, migrations, ORM, FK, admin, groups | [`artifacts/models.py`](apps/artifacts/models.py), `migrations/`, [`admin.py`](apps/artifacts/admin.py), Moderators group created by a data migration |
| VI | Cookies, sessions, users, login/logout | theme cookie (`set_theme`), `request.session["recent_artifacts"]`, `LoginView/LogoutView`, `@login_required`, permission `can_moderate` |

### Handy shell demo for Unit V (ORM)

```bash
python manage.py shell
>>> from apps.artifacts.models import Artifact, Category
>>> Artifact.objects.approved().count()
>>> Artifact.objects.filter(era__icontains="mughal").values_list("title", flat=True)
>>> Category.objects.get(name="Textile").artifacts.all()      # reverse foreign key
>>> a = Artifact.objects.first(); a.likes.count(); a.comments.all()
>>> a.title = "New title"; a.save()                            # update
>>> Artifact.objects.filter(status="rejected").delete()        # delete
```

## How the moderation flow works

```
 submit form -> validation (ModelForm + image validator) -> save -> screen_artifact()
                                                                   |
                    score >= 70 ---------------------------------> approved (public)
                    score <= 20 ---------------------------------> rejected (owner sees why)
                    otherwise  ----------------------------------> pending -> moderator queue
 editing title/description/image/category/era/region sends the artifact through screening again
```

Visibility rule: approved artifacts are public; pending/rejected ones are visible only to their owner
and moderators (everyone else gets a 404, so their existence is not revealed).

## Project layout

```
config/            settings, root urls, wsgi/asgi
apps/
  accounts/        signup, login, profile (User + Profile one-to-one, created by a signal)
  artifacts/       Category, Artifact, Comment, moderation rules, validators, seed command
  curation/        Collection (many-to-many with Artifact)
templates/         base.html, partials/, one folder per app, 403/404/500
static/css/        hand-written stylesheet with light/dark variables
```

## Security notes

CSRF tokens on every POST form; passwords hashed by Django; uploads validated by size, type and decoded
as real images; `next` redirects are checked with `url_has_allowed_host_and_scheme`; object-level checks
(owner / moderator) on edit, delete and collection changes. Before deploying set
`DJANGO_DEBUG=False`, a real `DJANGO_SECRET_KEY`, and `DJANGO_ALLOWED_HOSTS`.
