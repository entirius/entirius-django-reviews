# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Characterization of today's reviews key contract (X-API-KEY on the PATCH moderation route).

The key alone moderates a review (status included) — no customer JWT, no channel. Pins what the keyed route
answers — quirks included — so moving the key check onto another key store cannot change a status or a body.
Keys come only from the ``make_api_key`` helper.
"""

import secrets

import pytest
from rest_framework.test import APIClient

from django_reviews.enum import ReviewType
from django_reviews.models import ProductRepresentation, Review

REVIEWS_URL = "/api/reviews/1/{channel_idx}/reviews/"


@pytest.fixture
def review(db):
    product = ProductRepresentation.objects.create(sku="KEY-001", average_rate=0, number_of_reviews=0)
    review = Review(product=product, name="Reviewer", title="Title", detail="Detail")
    review.save()  # Review.save() saves twice, so objects.create() (force_insert) cannot be used
    return review


def _moderate(review, key: str | None, channel_idx: str = "any-channel"):
    headers = {} if key is None else {"HTTP_X_API_KEY": key}
    url = f"{REVIEWS_URL.format(channel_idx=channel_idx)}{review.uuid}/"
    return APIClient().patch(url, {"status": ReviewType.ACCEPTED}, format="json", **headers)


def _refusal(response) -> tuple[int, str, object]:
    body = response.json()
    return response.status_code, body["meta"]["status"], body["data"]


@pytest.fixture(autouse=True)
def _live_key(make_api_key):
    """Valid keys exist in every test, so a refusal proves the lookup, not an empty key store."""
    make_api_key()


@pytest.mark.django_db
class TestModerationKey:
    def test_no_key_is_401(self, review):
        assert _refusal(_moderate(review, None)) == (401, "UNAUTHORIZED", "Invalid api key")

    def test_wrong_key_is_refused_like_no_key(self, review):
        wrong_key = secrets.token_hex(32)
        response = _moderate(review, wrong_key)
        assert _refusal(response) == _refusal(_moderate(review, None))
        assert wrong_key not in response.content.decode()
        review.refresh_from_db()
        assert review.status == ReviewType.PENDING

    def test_right_key_moderates(self, review, make_api_key):
        response = _moderate(review, make_api_key())
        assert response.status_code == 200
        review.refresh_from_db()
        assert review.status == ReviewType.ACCEPTED

    def test_key_is_not_bound_to_a_channel(self, review, make_api_key):
        assert _moderate(review, make_api_key(), channel_idx="other-channel").status_code == 200


@pytest.mark.django_db
def test_public_review_listing_answers_without_a_key(review):
    response = APIClient().get(
        REVIEWS_URL.format(channel_idx="any-channel"), {"sku": "KEY-001", "page": 1, "limit": 10}
    )
    assert response.status_code == 200
