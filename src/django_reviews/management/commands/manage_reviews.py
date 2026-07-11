# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from bievents import bi_django_command_decorator
from django.core.management.base import BaseCommand

from django_reviews.worker.manage_reviews import calculate_reviews, send_unsent_reviews_to_magento


class Command(BaseCommand):
    help = "Calculate Reviews Details"

    @bi_django_command_decorator
    def handle(self, *args, **options):
        self.stdout.write("Start calculate Reviews details")
        calculate_reviews()
        self.stdout.write("Attempt to send unsent reviews to magento")
        send_unsent_reviews_to_magento()
