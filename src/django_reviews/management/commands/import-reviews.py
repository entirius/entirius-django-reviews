# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from process_logger import ProcessLogger

from django_reviews.domain.importers.review_importer import ReviewImporter
from django_reviews.enum import ReviewType


class Command(BaseCommand):
    help = "Import reviews from CSV file"
    logger = ProcessLogger("IMPORT_REVIEWS_COMMAND", "django_reviews")

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str, help="Path to CSV file with reviews")
        parser.add_argument("--delimiter", type=str, default=",", help="CSV delimiter (default: ,)")
        parser.add_argument(
            "--batch-size", type=int, default=1000, help="Batch size for bulk operations (default: 1000)"
        )
        parser.add_argument(
            "--default-status",
            type=str,
            default=ReviewType.ACCEPTED,
            choices=ReviewType.values,
            help=f"Default status for reviews without status column (default: {ReviewType.ACCEPTED})",
        )
        parser.add_argument(
            "--source",
            type=str,
            default=f"csv-import-{datetime.now().timestamp()}",
            help="Source for reviews (default: csv-import-YYYY-MM-DD HH:MM:SS)",
        )

    def handle(self, *args, **options):
        file_path = options["file_path"]
        delimiter = options["delimiter"]
        batch_size = options["batch_size"]
        default_status = options["default_status"]
        source = options["source"]

        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            raise CommandError(f"File not found: {file_path}")

        try:
            self.logger.info(f"Starting import from {file_path}")
            importer = ReviewImporter(
                filename=file_path,
                batch_size=batch_size,
                delimiter=delimiter,
                default_status=default_status,
                source=source,
            )

            result = importer.import_reviews()

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully imported {result['reviews_created']} reviews and {result['rates_created']} ratings"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Found {result['products_found']} existing products, created {result['products_not_found']} new products"
                )
            )
            self.stdout.write(self.style.SUCCESS(f"Found and linked {result['customers_found']} customers by email"))

        except Exception as e:
            self.logger.error(f"Error during import: {str(e)}")
            raise CommandError(f"Error during import: {str(e)}")
