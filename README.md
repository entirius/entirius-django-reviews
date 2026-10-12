# entirius-django-reviews

A Django module for product reviews and ratings in Entirius, the open-source modular ecommerce platform. It gives
the storefront a REST API to submit and list reviews, lets staff moderate them, keeps an average rating per
product, and can export reviews to Magento.

[![PyPI](https://img.shields.io/pypi/v/entirius-django-reviews.svg)](https://pypi.org/project/entirius-django-reviews/)
[![Python](https://img.shields.io/pypi/pyversions/entirius-django-reviews.svg)](https://pypi.org/project/entirius-django-reviews/)
[![License: MPL-2.0](https://img.shields.io/badge/license-MPL--2.0-blue.svg)](https://github.com/entirius/entirius-django-reviews/blob/develop/LICENSE)

## What it does

- Accepts reviews with one or more rating criteria and lists them per sales channel.
- Moderates reviews in the Django admin and over a key-protected API.
- Recalculates the average rating and the number of reviews per product.
- Imports reviews and ratings from CSV.
- Exports reviews to Magento when the `magento` extra is installed.

## Installation

```shell
uv add entirius-django-reviews
pip install entirius-django-reviews
```

```python
INSTALLED_APPS = [
    ...
    "django_utils",
    "django_pim",
    "django_accounts",
    "django_reviews",
]

# urls.py
urlpatterns = [
    path("", include("django_reviews.urls")),
]
```

Required settings: `BI_ENVIRONMENT` and `BI_BUSINESS_UNIT` (read at import). Every other setting has a default;
reference: https://github.com/entirius/entirius-django-reviews/blob/develop/AGENTS.md (section Settings).

The Magento export is an extra:

```shell
uv add "entirius-django-reviews[magento]"
```

Moderation calls send the key in the `X-API-KEY` header. Where `django_access` is installed the key is an access
token with the scope `reviews.moderate`:

```shell
python manage.py access_token create --application reviews-moderation --create-application --scope reviews.moderate --channel default
```

Without `django_access`, `python manage.py reviews-generate-api-key` creates the key.

## Quick start

```python
from django_reviews.worker.manage_reviews import calculate_reviews

calculate_reviews()  # recalculate average ratings from the accepted reviews
```

## Requirements

- Python 3.11 or newer, Django 5.0 or newer.
- Entirius packages pulled in: `entirius-django-utils`, `entirius-django-pim`, `entirius-django-accounts`,
  `entirius-py-bievents`, `entirius-py-process-logger`.

## Documentation

- Module docs: https://github.com/entirius/entirius-django-reviews/tree/develop/docs
- Entirius documentation: https://docs.entirius.com/
- Changelog: https://github.com/entirius/entirius-django-reviews/blob/develop/CHANGELOG.md

## Part of Entirius

This module runs inside the Entirius backend service (Volkanos), next to the product and customer account modules.

- Backend service: https://github.com/entirius/entirius-service-volkanos
- Docker harness: https://github.com/entirius/entirius-zeno
- Sibling modules: https://github.com/entirius/entirius-django-pim, https://github.com/entirius/entirius-django-accounts,
  https://github.com/entirius/entirius-django-access

## Development

```shell
make install     # sync dependencies (uv)
make check       # lint + format check (ruff)
make test        # test suite (pytest + pytest-django)
```

Development and agent instructions: https://github.com/entirius/entirius-django-reviews/blob/develop/AGENTS.md

## License

Mozilla Public License 2.0 (MPL-2.0) — see https://github.com/entirius/entirius-django-reviews/blob/develop/LICENSE.
