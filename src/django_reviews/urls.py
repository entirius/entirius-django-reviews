# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django.urls import include, path

from django_reviews import settings
from django_reviews.views.review import modify_review, reviews_view

api_paths = [
    path("reviews/", reviews_view, name="get_or_create_reviews_view"),
    path("reviews/<str:uuid>/", modify_review, name="modify_reviews"),
]

urlpatterns = [path(f"{settings.BASE_URL}/reviews/<str:version>/<str:channel_idx>/", include(api_paths))]
