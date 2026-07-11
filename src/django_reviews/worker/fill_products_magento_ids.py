# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import csv
import logging
from typing import AnyStr

from django.db import IntegrityError

from django_reviews.models.product_representation import ProductRepresentation

logger_process = logging.getLogger("process")


def read_from_csv(absolute_path: AnyStr) -> (list, AnyStr):
    if absolute_path is not None:
        path = absolute_path
    else:
        return [], "Need to define csv path"
    with open(path) as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        data = []
        for row in reader:
            row_dict = {}
            for h, v in zip(headers, row):
                if v is None:
                    v = ""
                row_dict[h] = v
            data.append(row_dict)
    return data, "Loaded"


def creating_in_db_for_each_line(data):
    errors = 0
    number_ids_csv = len(data)
    products_to_update = []
    for row, product_data in enumerate(data):
        magento_id = product_data.get("id", None)
        product_sku = product_data.get("sku", None)
        if not magento_id or not product_sku:
            errors += 1
            logger_process.error(
                "Record skip. Data needed",
                extra={"details": {"row": row, "magento_id": magento_id, "product_sku": product_sku}},
            )
            continue

        products_sku = ProductRepresentation.objects.filter(sku=product_sku)
        if products_sku:
            for product in products_sku:
                products_to_update.append(ProductRepresentation(id=product.id, magento_id=magento_id))
        else:
            errors += 1
            logger_process.error(
                "Record skip. This sku doesn't exists in ProductRepresentation",
                extra={"details": {"row": row, "magento_id": magento_id, "product_sku": product_sku}},
            )
    if products_to_update:
        try:
            ProductRepresentation.objects.bulk_update(products_to_update, ["magento_id"], batch_size=10000)
        except IntegrityError:
            error_list = []
            for product_to_update in products_to_update:
                try:
                    product_to_update.save(update_fields=["magento_id"])
                except IntegrityError as e:
                    errors += 1
                    error_sku_data = {
                        "sku": product_to_update.sku,
                        "name": product_to_update.name,
                        "message": str(e),
                    }
                    error_list.append(error_sku_data)
                if error_list:
                    logger_process.error(
                        "Errors while importing magento_id's", extra={"details": {"error_list": error_list}}
                    )
    else:
        logger_process.info("Nothing to update", extra={"details": {"data": data}})

    return errors, number_ids_csv


def import_ids_from_csv(file_path: str):
    data, msg = read_from_csv(file_path)
    errors, number_ids_csv = creating_in_db_for_each_line(data)
    return errors, number_ids_csv
