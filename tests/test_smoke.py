# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Smoke test: every public submodule imports cleanly under a configured Django."""

import importlib

import pytest

MODULES = [
    "django_reviews.apps",
    "django_reviews.settings",
    "django_reviews.bi",
    "django_reviews.enum",
    "django_reviews.urls",
    "django_reviews.admin",
    "django_reviews.models",
    "django_reviews.models.apikey",
    "django_reviews.models.review",
    "django_reviews.models.product_representation",
    "django_reviews.domain.dto.product_representation",
    "django_reviews.domain.dto.review",
    "django_reviews.domain.importers.review_importer",
    "django_reviews.utils.decorators",
    "django_reviews.utils.pagination",
    "django_reviews.views.review",
    "django_reviews.worker.fill_products_magento_ids",
    "django_reviews.worker.fill_reviews_product_representation",
    "django_reviews.worker.manage_reviews",
    "django_reviews.management.commands.import-reviews",
    "django_reviews.management.commands.fill-reviews-product-representation-from-pim",
    "django_reviews.management.commands.fill-reviews-products-magento-id",
    "django_reviews.management.commands.reviews-generate-api-key",
    "django_reviews.management.commands.manage_reviews",
]


@pytest.mark.parametrize("module", MODULES)
def test_module_imports(module):
    importlib.import_module(module)
