# AGENTS.md

Product reviews and ratings — distribution `entirius-django-reviews`, Django app `django_reviews`.

## Commands

| Command | Meaning |
|---|---|
| `make install` | sync dependencies (uv, incl. extras) |
| `make check` | lint + format-check (ruff) |
| `make fix` | auto-fix lint + format |
| `make test` | test suite (pytest + pytest-django) |

## Conventions

- English only: code, docs, commits, branches, PRs.
- MPL-2.0: every non-trivial source file carries the license header (pre-commit inserts it).
- Toolchain: uv + ruff + hatchling + pytest; all config in `pyproject.toml`; `uv.lock` committed.
- Git flow: `master` (production) + `develop` (integration); changes land via PR; semver tag on `master`.
- Never rename the package / Django app_label / DB table prefix `django_reviews` — it is a schema contract.
- Migrations are part of the public contract — never edit an already released migration.
- Default: do not commit — git is the user's call.

## Architecture

- **Models** (`models/`): `Review` (FK `product` → `ProductRepresentation`, FK `customer` →
  `django_accounts.Customer`, nullable), `Rate` (per-criterion rating, FK → `Review`),
  `ProductRepresentation` (SKU/name read model reviews attach to), `APIKey` (X-API-KEY auth).
- **API** (`views/`, `urls/`): built on `django_utils.api` (decorators, exceptions, paginated
  responses) — not DRF. Public GET listing + authenticated submit/patch.
- **Admin** (`admin.py`): moderation of reviews and CSV import of ratings.
- **Domain** (`domain/`): marshmallow-dataclass DTOs and the review importer.
- **Workers** (`worker/`): average-rating recalculation and read-model fill from PIM.
- **BI** (`bi.py`): `bievents` events for review calculations and Magento sends.

## Integration points

- `entirius-django-accounts` (**required**) — `Review.customer` FK; the importer resolves a
  `Customer` by e-mail (soft, `try/except ImportError`).
- `entirius-django-pim` (**required**) — `fill-reviews-product-representation-from-pim` command
  builds the read model from PIM products.
- `entirius-py-magento2-sdk2` (extra `magento`) — `Review.send_to_magento` pushes reviews when installed.
- `entirius-django-checkout` — `Channel` used only as a `TYPE_CHECKING` type hint (no runtime dependency).

## Settings Reference

Read via `getattr(settings, ...)` (see `settings.py`), all with defaults:

| Setting | Default | Meaning |
|---|---|---|
| `MAX_REVIEW_DETAIL_LENGTH` | `4000` | max review body length |
| `MAX_REVIEW_TITLE_LENGTH` | `128` | max review title length |
| `RATINGS_NAME` | `["rating"]` | allowed rating criteria |
| `AVAILABLE_REVIEW_SOURCE` | `["self/volkanos"]` | allowed review sources |
| `MAX_RATE` | `5` | max rating value |
| `API_BASE_URL` | `"api"` | API path prefix |
| `OVERWRITE_RATES` | `False` | PATCH overwrites ratings vs. appends |
| `MAGENTO2_URL_FOR_CHECKOUT_EXPORT` | `None` | Magento base URL for review export |
| `MAGENTO2_TOKEN_FOR_CHECKOUT_EXPORT` | `None` | Magento token for review export |
| `FIRST_PLUS_LASTNAME_WHEN_REVIEW_NAME_BLANK` | `False` | derive author name from customer |
| `FILL_BLANK_NAME_AS_N_SLASH_A` | `False` | fall back to `n/a` for blank author name |
| `BI_ENVIRONMENT` / `BI_BUSINESS_UNIT` | — | required by `bi.py` at import time |
