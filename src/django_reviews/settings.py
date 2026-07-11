# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django.conf import settings

MAX_REVIEW_DETAIL_LENGTH = getattr(settings, "MAX_REVIEW_DETAIL_LENGTH", 4000)
MAX_REVIEW_TITLE_LENGTH = getattr(settings, "MAX_REVIEW_TITLE_LENGTH", 128)
RATINGS_NAME = getattr(settings, "RATINGS_NAME", ["rating"])
AVAILABLE_REVIEW_SOURCE = getattr(settings, "AVAILABLE_REVIEW_SOURCE", ["self/volkanos"])
MAX_RATE = getattr(settings, "MAX_RATE", 5)
BASE_URL = getattr(settings, "API_BASE_URL", "api").strip("/")
OVERWRITE_RATES = getattr(settings, "OVERWRITE_RATES", False)
MAGENTO_URL = getattr(settings, "MAGENTO2_URL_FOR_CHECKOUT_EXPORT", None)
MAGENTO_TOKEN = getattr(settings, "MAGENTO2_TOKEN_FOR_CHECKOUT_EXPORT", None)
FIRST_PLUS_LASTNAME_WHEN_REVIEW_NAME_BLANK = getattr(settings, "FIRST_PLUS_LASTNAME_WHEN_REVIEW_NAME_BLANK", False)
FILL_BLANK_NAME_AS_N_SLASH_A = getattr(settings, "FILL_BLANK_NAME_AS_N_SLASH_A", False)
