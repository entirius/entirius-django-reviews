# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class ReviewType(TextChoices):
    PENDING = "pending", _("Pending")
    ACCEPTED = "accepted", _("Accepted")
    NOT_ACCEPTED = "not_accepted", _("Not Accepted")
    ARCHIVED = "archived", _("Archived")

    @staticmethod
    def map(choice: int) -> int:
        match choice:
            case ReviewType.PENDING:
                return 2
            case ReviewType.ACCEPTED:
                return 1
            case ReviewType.PENDING:
                return 3
            case _:
                return 3
