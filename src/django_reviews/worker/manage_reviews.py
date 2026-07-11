# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from decimal import Decimal
from itertools import groupby
from statistics import mean

from django_reviews.bi import CalculateSingleProductReviewsDetailsEvent, SendUnsentReviewsToMagentoEvent
from django_reviews.enum import ReviewType
from django_reviews.models import ProductRepresentation, Review, ReviewType


def calculate_reviews():
    bev = CalculateSingleProductReviewsDetailsEvent(is_ongoing_event=True)
    reviews_accepted = Review.objects.filter(status=ReviewType.ACCEPTED).order_by("product")
    grouped_product_reviews = {k: list(v) for k, v in groupby(reviews_accepted, key=lambda x: x.product)}
    numbers_of_product = 0
    product_processed = []
    if grouped_product_reviews:
        for product, reviews in grouped_product_reviews.items():
            numbers_of_product += 1
            bev_product = CalculateSingleProductReviewsDetailsEvent(is_ongoing_event=True)
            report = {"sku": product.sku}
            try:
                for review in reviews:
                    review.calculate_average_rate()
                product.number_of_reviews = len(reviews)
                product.average_rate = float(round(mean([Decimal(review.average_rate) for review in reviews]), 2))
                product.save()
                product_processed.append(product.sku)
                report["number_of_product_reviews"] = product.number_of_reviews
                report["average_rate"] = product.average_rate
                bev_product.set_details(report)
                bev_product.finish_with_success(
                    finish_tag=f"Details for product sku: {product.sku} successfully calculated"
                )
            except Exception as e:
                bev_product.set_details(report)
                bev_product.finish_with_exception(e)
        bev.set_details({"numbers_of_product": numbers_of_product})
        bev.finish_with_success(finish_tag="Products reviews details has been filled")
    else:
        bev.set_details({"numbers_of_product": numbers_of_product})
        bev.finish_with_success(finish_tag="Zero accepted reviews.")

    ProductRepresentation.objects.exclude(sku__in=product_processed).update(number_of_reviews=0, average_rate=0)


def send_unsent_reviews_to_magento():
    bev = SendUnsentReviewsToMagentoEvent(is_ongoing_event=True)
    unsent_reviews = Review.objects.filter(is_sent_to_magento=False)
    for review in unsent_reviews:
        review.send_to_magento()
    bev.finish_with_success(finish_tag="Unsent reviews attempted to send to magento")
