# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The key admin on either path (with or without django_access): only the last four characters, no key search."""

import os
from importlib.util import find_spec

import pytest
from django.contrib import admin
from django.core.management import call_command

from django_reviews.models import APIKey


@pytest.mark.django_db
def test_key_admin_never_shows_the_raw_key(admin_user, rf, settings):
    settings.ROOT_URLCONF = "tests.admin_urls"
    key = APIKey.objects.create()
    model_admin = admin.site.get_model_admin(APIKey)
    request = rf.get("/")
    request.user = admin_user
    assert not model_admin.get_search_fields(request)
    for response in (model_admin.changelist_view(request), model_admin.change_view(request, str(key.pk))):
        html = response.render().content.decode()
        assert response.status_code == 200
        assert key.key not in html
        assert f"…{key.key[-4:]}" in html


legacy_only = pytest.mark.skipif(
    find_spec("django_access") is not None and not os.environ.get("ENTIRIUS_TEST_NO_ACCESS"),
    reason="legacy path only",
)


@legacy_only
@pytest.mark.django_db
def test_legacy_key_admin_stays_editable(admin_user, rf):
    key = APIKey.objects.create()
    model_admin = admin.site.get_model_admin(APIKey)
    request = rf.get("/")
    request.user = admin_user
    assert model_admin.has_add_permission(request)
    assert model_admin.has_change_permission(request, key)
    assert model_admin.has_delete_permission(request, key)


@legacy_only
@pytest.mark.django_db
def test_legacy_command_still_creates_a_key(tmp_path):
    key_file = tmp_path / "key"
    call_command("reviews-generate-api-key", file_path=str(key_file))
    assert APIKey.objects.get().key == key_file.read_text()
