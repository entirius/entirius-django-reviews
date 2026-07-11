# entirius-django-reviews

Product reviews and ratings for Django.

A REST API for submitting and listing product reviews, admin moderation, average-rating
aggregation per product, and optional export of reviews to Magento.

## Installation

```shell
pip install entirius-django-reviews
```

Add `django_reviews` to `INSTALLED_APPS` and include `django_reviews.urls`.

The `Review` model references `django_accounts.Customer`, so `entirius-django-accounts`
must be installed and migrated. Magento export is optional:

```shell
pip install "entirius-django-reviews[magento]"
```

## Development

```shell
uv sync --all-extras
make check test
```

See [AGENTS.md](AGENTS.md) for architecture, settings and integration points.
