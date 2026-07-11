# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging

from django.db import IntegrityError, models

from django_reviews.domain.dto.product_representation import ProductRepresentation as ProductRepresentationDTO

logger_process = logging.getLogger("process")


class ProductRepresentation(models.Model):
    sku = models.CharField(max_length=128, null=False)
    name = models.CharField(max_length=2048, null=True, blank=True)
    average_rate = models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, default=0)
    number_of_reviews = models.DecimalField(blank=True, decimal_places=0, max_digits=6, null=True, default=0)
    magento_id = models.IntegerField(db_index=True, null=True, blank=True)
    objects = models.Manager()

    def __str__(self) -> str:
        return f"{self.sku}"

    class Meta:
        ordering = ["sku"]
        verbose_name_plural = "products reviews details"

    @staticmethod
    def bulk_update_or_create(products: list[ProductRepresentationDTO]):
        logger_process.info(f"Reviews Product Bulk Save is starting for {len(products)} products")

        records_to_update = []
        records_to_create = []
        fields_to_update = ["name"]

        cnt = 0
        total = len(products)
        for product in products:
            cnt += 1

            kwargs = {}
            find = ProductRepresentation.objects.filter(sku=product.sku).first()
            if find is None:
                records_to_create.append(ProductRepresentation(sku=product.sku, name=product.name, **kwargs))
            else:
                records_to_update.append(
                    ProductRepresentation(id=find.id, sku=product.sku, name=product.name, **kwargs)
                )
            if cnt % 1000 == 0:
                logger_process.info(f"Reviews Product Bulk Save collecting progress {cnt} / {total}")
        logger_process.info(f"Reviews Product Bulk Save starting bulk update for {len(records_to_update)} products")

        # updating data
        try:
            ProductRepresentation.objects.bulk_update(records_to_update, ["sku"] + fields_to_update, batch_size=10000)
        except IntegrityError:
            error_list = []
            for record_to_update in records_to_update:
                try:
                    record_to_update.save(update_fields=["sku"] + fields_to_update)
                except IntegrityError as e:
                    error_sku_data = {"sku": record_to_update.sku, "message": str(e)}
                    error_list.append(error_sku_data)
            logger_process.error(
                "List of errors during updating Reviews ProductRepresentation",
                extra={"details": {"error_list": error_list}},
            )
        logger_process.info(f"Reviews Product Bulk Save starting bulk create for {len(records_to_create)} products")

        # creating data
        try:
            ProductRepresentation.objects.bulk_create(records_to_create, batch_size=1000)
        except IntegrityError:
            error_list = []
            for record_to_create in records_to_create:
                try:
                    record_to_create.save()
                except IntegrityError as e:
                    error_sku_data = {"sku": record_to_create.sku, "message": str(e)}
                    error_list.append(error_sku_data)
            logger_process.error(
                "List of errors during creating Reviews ProductRepresentation",
                extra={"details": {"error_list": error_list}},
            )

        logger_process.info("Reviews Product Bulk Save is done")
        return len(records_to_create), len(records_to_update)
