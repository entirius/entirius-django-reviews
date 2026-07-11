# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import json
import logging
import uuid
from dataclasses import asdict
from decimal import Decimal
from statistics import mean

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django_utils.api.exceptions import BadRequest

from django_reviews.enum import ReviewType
from django_reviews.models import ProductRepresentation
from django_reviews.settings import (
    FIRST_PLUS_LASTNAME_WHEN_REVIEW_NAME_BLANK,
    MAGENTO_TOKEN,
    MAGENTO_URL,
    MAX_REVIEW_DETAIL_LENGTH,
    MAX_REVIEW_TITLE_LENGTH,
    RATINGS_NAME,
)

logger = logging.getLogger("process")


class Review(models.Model):
    name = models.CharField(max_length=256, blank=True, null=True)
    product: "ProductRepresentation" = models.ForeignKey(
        "ProductRepresentation", related_name="review_products", blank=False, on_delete=models.deletion.CASCADE
    )
    customer: "Customer" = models.ForeignKey(
        "django_accounts.Customer", blank=True, null=True, on_delete=models.SET_NULL
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=128, default=ReviewType.PENDING, choices=ReviewType.choices)
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)
    channel_idx = models.CharField(blank=True, max_length=256, null=True)
    title = models.CharField(
        blank=True, max_length=512, null=True
    )  # length większy niż z założenia, bo settings będzie definować długość
    detail = models.CharField(
        blank=True, max_length=8000, null=True
    )  # length większy niż z założenia, bo settings będzie definować długość
    average_rate = models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)
    source = models.CharField(blank=True, max_length=256, null=True)
    is_sent_to_magento = models.BooleanField(default=False)
    objects = models.Manager()

    class Meta:
        ordering = ["-created_at"]

        unique_together = (
            "product",
            "customer",
        )

    @classmethod
    def create(cls, product: "ProductRepresentation" = None, customer=None, *args, **kwargs):
        return cls(product=product, customer=customer, *args, **kwargs)

    def calculate_average_rate(self):
        rates = [Decimal(rate.rate) for rate in self.review_rate.all()]
        if rates:
            self.average_rate = float(round(mean(rates), 2))
        super().save()

    def save(self, *args, **kwargs):
        if len(str(self.title)) > MAX_REVIEW_TITLE_LENGTH:
            raise BadRequest(f"The review title should be shorter than {MAX_REVIEW_TITLE_LENGTH} characters.")

        if len(str(self.detail)) > MAX_REVIEW_DETAIL_LENGTH:
            raise BadRequest(f"The review detail should be shorter than {MAX_REVIEW_DETAIL_LENGTH} characters.")

        super().save(*args, **kwargs)
        self.calculate_average_rate()
        super().save(*args, **kwargs)

    def send_to_magento(self):
        review_send_to_magento = False
        data = None
        try:
            from magento2_sdk2.dto.review import ReviewDetailsPayload, ReviewPayload, ReviewRatesPayload
            from magento2_sdk2.services.client import Magento2Client
            from magento2_sdk2.services.worker import create_review

            name = ""
            if self.name:
                name = self.name
            else:
                if FIRST_PLUS_LASTNAME_WHEN_REVIEW_NAME_BLANK:
                    name = f"{self.customer.first_name} {self.customer.last_name}"

            magento_client: Magento2Client = Magento2Client(base_url=MAGENTO_URL, access_token=MAGENTO_TOKEN)
            data = ReviewPayload(
                ReviewDetailsPayload(
                    uuid=str(self.uuid),
                    title=str(self.title),
                    detail=str(self.detail),
                    nickname=name,
                    ratings=[
                        ReviewRatesPayload(rating_name=rate.rating_name, value=str(rate.rate))
                        for rate in self.review_rate.all()
                    ],
                    review_entity="product",
                    review_status=ReviewType.map(self.status),
                    entity_pk_value=self.product.magento_id,
                )
            )
            logger.debug("Making request to magento with reviews", extra={"request_payload": json.dumps(asdict(data))})

            if not self.product.magento_id:
                logger.error("Magento error. This product doesn't have magento_id. Sending to magento skipping")
                return data

            try:
                create_review(magento_client, data)
                review_send_to_magento = True
            except Exception as e:
                logger.exception(e)

        except ImportError as e:
            logger.exception(e)
        except Exception as e:
            logger.exception(e)
        self.is_sent_to_magento = review_send_to_magento
        self.save()
        return data


class Rate(models.Model):
    rate = models.FloatField(blank=True, null=True)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="review_rate")
    rating_name = models.CharField(blank=True, max_length=256, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

    def save(self, *args, **kwargs):
        if self.rating_name not in RATINGS_NAME:
            raise BadRequest("Rating name doesn't allowed by setting RATINGS_NAME")
        super().save(*args, **kwargs)


@receiver(post_save, sender=Rate, dispatch_uid="update_average_rate")
def update_average_rate(sender, instance, **kwargs):
    instance.review.calculate_average_rate()
