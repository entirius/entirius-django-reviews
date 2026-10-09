# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import secrets

import pytest
from django.apps import apps


def import_keys_into_access() -> None:
    """With django_access installed keys are tokens: import the legacy rows as a deploy's migrate does."""
    if apps.is_installed("django_access"):
        from django_access.services.legacy import import_legacy_keys

        import_legacy_keys()


@pytest.fixture
def make_api_key(db):
    """Create an X-API-KEY the module accepts today and return its raw value.

    reviews keys carry no channel and no scope, so both arguments are accepted and ignored. The key contract tests
    go through this helper only (with django_access installed it also imports the key as a legacy token), so moving
    the check onto another key store changes this function, never the assertions. Values are random and never printed.
    """
    from django_reviews.models import APIKey

    def make_api_key(channel=None, scope: str | None = None) -> str:
        raw = secrets.token_hex(32)
        APIKey.objects.create(key=raw)
        import_keys_into_access()
        return raw

    return make_api_key


@pytest.fixture
def review(db):
    from django_reviews.models import ProductRepresentation, Review

    product = ProductRepresentation.objects.create(sku="KEY-001", average_rate=0, number_of_reviews=0)
    review = Review(product=product, name="Reviewer", title="Title", detail="Detail")
    review.save()  # Review.save() saves twice, so objects.create() (force_insert) cannot be used
    return review
