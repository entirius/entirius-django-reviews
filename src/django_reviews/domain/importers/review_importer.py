# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import csv
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from django.utils import timezone
from django.utils.timezone import make_aware
from process_logger import ProcessLogger, ProcessLoggerMixin
from tqdm import tqdm

from django_reviews.enum import ReviewType
from django_reviews.models import ProductRepresentation, Rate, Review


@dataclass
class ReviewImportColumn:
    name: str
    required: bool = False
    default: Any = None


class ReviewImporter(ProcessLoggerMixin):
    COLUMNS = {
        "sku": ReviewImportColumn(name="sku", required=True),
        "name": ReviewImportColumn(name="name"),
        "title": ReviewImportColumn(name="title"),
        "detail": ReviewImportColumn(name="detail"),
        "status": ReviewImportColumn(name="status"),
        "source": ReviewImportColumn(name="source"),
        "email": ReviewImportColumn(name="email"),
        "created_at": ReviewImportColumn(name="created_at"),
    }

    def __init__(
        self,
        filename: str,
        batch_size: int = 1000,
        delimiter: str = ",",
        default_status: str = ReviewType.ACCEPTED,
        source: str = f"csv-import-{datetime.now().timestamp()}",
    ):
        self.rating = None
        self.filename = filename
        self.batch_size = batch_size
        self.source = source
        self.delimiter = delimiter
        self.default_status = default_status
        self.logger = ProcessLogger("REVIEW_IMPORT", "django_reviews")

    def find_rating_column(self, headers: list[str]) -> list[str]:
        self.rating = []
        for header in headers:
            if header.lower().startswith("rating."):
                self.rating.append(header)
        if not self.rating:
            error_msg = "No rating columns found in CSV file. Rating columns should start with 'rating.[name]'."
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        return self.rating

    def validate_csv_columns(self, headers: list[str]) -> None:
        self.find_rating_column(headers)
        required_columns = [col.name for col in self.COLUMNS.values() if col.required]
        missing_columns = [col for col in required_columns if col not in headers]

        if missing_columns:
            error_msg = f"Missing required columns in CSV file: {', '.join(missing_columns)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

    def get_default_values(self) -> dict[str, Any]:
        return {key: col.default for key, col in self.COLUMNS.items() if col.default is not None}

    def read_csv_rows(self) -> Iterator[dict[str, str]]:

        try:
            with open(self.filename, encoding="utf-8") as csv_file:
                reader = csv.DictReader(csv_file, delimiter=self.delimiter)
                self.validate_csv_columns(reader.fieldnames)

                for row in reader:
                    yield row
        except Exception as e:
            self.logger.error(f"Error reading CSV file: {str(e)}")
            raise

    def process_csv_file(self) -> dict[str, int]:
        reviews_created = 0
        rates_created = 0
        products_found = 0
        products_not_found = 0
        customers_found = 0
        try:
            rows = list(self.read_csv_rows())
            total_rows = len(rows)

            rows_batched = [rows[i : i + self.batch_size] for i in range(0, total_rows, self.batch_size)]
            for rows in tqdm(rows_batched, desc="Processing batches", leave=False):
                reviews_to_create = []
                rates_to_create = []
                for row in tqdm(rows, desc="Processing reviews", leave=False):
                    sku = row.get("sku")
                    self.logger.add_log_param("sku", sku)

                    if not sku:
                        self.logger.warning("Skipping row without SKU")
                        continue

                    product = ProductRepresentation.objects.filter(sku=sku).first()
                    if not product:
                        self.logger.warning(f"Product with SKU {sku} not found, creating new product")
                        product = ProductRepresentation(sku=sku, name=row.get("product_name", ""))
                        product.save()
                        products_not_found += 1
                    else:
                        products_found += 1

                    customer = None
                    email = row.get("email")
                    if email:
                        try:
                            from django_accounts.models import Customer

                            customer = Customer.objects.filter(user__email=email).first()
                            if customer:
                                customers_found += 1
                                self.logger.info(f"Found customer with email {email}")
                            else:
                                self.logger.warning(f"Customer with email {email} not found")
                        except ImportError:
                            self.logger.warning("Could not import Customer model from django_accounts")

                    created_at = row.get("created_at", None)
                    if created_at:
                        if created_at.isdigit():
                            try:
                                created_at_datetime = datetime.fromtimestamp(int(created_at))
                                created_at_datetime = make_aware(created_at_datetime)
                                created_at = created_at_datetime
                            except ValueError:
                                self.logger.warning(f"Invalid created_at value in row for SKU {sku}: {created_at}")
                                created_at = timezone.now()
                        else:
                            try:
                                created_at_datetime = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                                created_at_datetime = make_aware(created_at_datetime)
                                created_at = created_at_datetime
                            except ValueError:
                                self.logger.warning(
                                    f"Invalid created_at string format in row for SKU {sku}: {created_at}"
                                )
                                created_at = timezone.now()
                    else:
                        created_at = timezone.now()

                    review = Review(
                        product=product,
                        customer=customer,
                        name=row.get("name", ""),
                        title=row.get("title", ""),
                        detail=row.get("detail", ""),
                        status=row.get("status", self.default_status),
                        source=row.get("source", self.source),
                        created_at=created_at if created_at else None,
                    )
                    reviews_to_create.append(review)

                    for rate_header in self.rating:
                        rate_value = row.get(rate_header)
                        if rate_value:
                            try:
                                rate_value = float(rate_value)
                                rate = Rate(
                                    rate=rate_value,
                                    rating_name=rate_header.split(".")[1],
                                )
                                rates_to_create.append((rate, review))
                            except ValueError:
                                self.logger.warning(f"Invalid rating value in row for SKU {sku}: {row.get('rating')}")

                review_created = []
                for review in reviews_to_create:
                    try:
                        review.save()
                        review_created.append(review)
                    except Exception as e:
                        self.logger.exception(e)

                if rates_to_create:
                    rates_batch = []
                    for rate, review in rates_to_create:
                        if review in review_created:
                            rate.review = review
                            rates_batch.append(rate)

                    if rates_batch:
                        Rate.objects.bulk_create(rates_batch, batch_size=self.batch_size, ignore_conflicts=True)
                        rates_created += len(rates_batch)

                        review_ids = [rate.review.id for rate in rates_batch]
                        for review in Review.objects.filter(id__in=review_ids).iterator():
                            review.calculate_average_rate()

        except Exception as e:
            self.logger.exception(e)
            raise

        return {
            "reviews_created": reviews_created,
            "rates_created": rates_created,
            "products_found": products_found,
            "products_not_found": products_not_found,
            "customers_found": customers_found,
        }

    def import_reviews(self) -> dict[str, int]:
        self.logger.info(f"Starting review import from {self.filename}")

        try:
            result = self.process_csv_file()
            self.logger.info(f"Import completed successfully: {result}")
            return result
        except Exception as e:
            self.logger.exception(e)
            raise
