# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging
from dataclasses import asdict

from django.db import transaction
from django.forms.models import model_to_dict
from django.views.decorators.csrf import csrf_exempt
from django_utils.api.decorators import (
    api_view,
    authenticate,
    parse_body,
    parse_parameters,
    require_authentication,
    require_http_method,
)
from django_utils.api.exceptions import BadRequest, NotFound
from django_utils.api.responses import PaginatedResponse, Response

from django_reviews.domain.dto.review import (
    ReviewDetailsResponse,
    ReviewParams,
    ReviewRequest,
    ReviewRequestPatch,
    ReviewResponse,
)
from django_reviews.models import ProductRepresentation, Rate, Review, ReviewType
from django_reviews.settings import (
    FILL_BLANK_NAME_AS_N_SLASH_A,
    FIRST_PLUS_LASTNAME_WHEN_REVIEW_NAME_BLANK,
    OVERWRITE_RATES,
)
from django_reviews.utils.decorators import authorize_api
from django_reviews.utils.pagination import paginate

logger = logging.getLogger("process")


@api_view
@csrf_exempt
@require_http_method("POST", "GET")
def reviews_view(request, channel_idx=None, *args, **kwargs):
    def map_objects(reviews_accepted):
        all_reviews = []
        for review in reviews_accepted:
            Rate.objects.filter()
            review_obj = ReviewResponse(
                name=review.name,
                sku=review.product.sku,
                title=review.title,
                detail=review.detail,
                created_at=review.created_at.strftime("%Y-%m-%d"),
                average_rate=review.average_rate,
                ratings=[
                    ReviewDetailsResponse(rate=rate.rate, rating_name=rate.rating_name)
                    for rate in review.review_rate.all()
                ],
            )
            all_reviews.append(asdict(review_obj))
        return all_reviews

    @parse_parameters(ReviewParams.Schema)
    def get(request, channel_idx: str, params: ReviewParams, *args, **kwargs):
        reviews_accepted = Review.objects.filter(
            status=ReviewType.ACCEPTED, product__sku__in=params.sku
        ).prefetch_related("review_rate")
        sorting_params = []
        if params.sort:
            for sorter in getattr(params, "sort", []):
                if sorter.field == "created_at":
                    sorter_direction = "-" if sorter.order == "DESC" else ""
                    sorting_params.append(f"{sorter_direction}{sorter.field}")
        else:
            sorting_params.append("created_at")
        if params.source:
            reviews_accepted = reviews_accepted.filter(source=params.source)
        reviews_accepted = reviews_accepted.order_by(*sorting_params)

        pagination, paginated_data = paginate(request.GET, reviews_accepted)
        map_reviews = map_objects(paginated_data)

        return PaginatedResponse(pagination, map_reviews)

    @authenticate
    @require_authentication
    @parse_body(ReviewRequest.Schema)
    def post(request, channel_idx, body: ReviewRequest, *args, **kwargs):
        customer = request.user.customer
        rate_payload = []
        if Review.objects.filter(customer=customer, product__sku=body.sku).exists():
            raise BadRequest("You can't add more than one review for one product.")

        with transaction.atomic():
            obj, created = ProductRepresentation.objects.get_or_create(
                sku=body.sku, defaults={"average_rate": 0, "number_of_reviews": 0}
            )
            number_of_rates = len(body.ratings)
            sum_of_rates = 0
            for rate in body.ratings:
                sum_of_rates += rate.rate

            if not body.name:
                if FIRST_PLUS_LASTNAME_WHEN_REVIEW_NAME_BLANK:
                    if not customer.user.first_name and not customer.user.last_name:
                        if FILL_BLANK_NAME_AS_N_SLASH_A:
                            body.name = "N/A"
                        else:
                            raise BadRequest("You must provide a name.")
                    else:
                        body.name = f"{customer.user.first_name} {customer.user.last_name}"
                else:
                    if FILL_BLANK_NAME_AS_N_SLASH_A:
                        body.name = "N/A"
                    else:
                        raise BadRequest("You must provide a name.")

            review = Review(
                name=body.name,
                product=obj,
                title=body.title,
                customer=customer,
                status=ReviewType.PENDING,
                detail=body.detail,
                channel_idx=channel_idx,
                source=body.source,
                average_rate=sum_of_rates / number_of_rates,
            )
            review.save()
            for rate in body.ratings:
                rates_for_review = Rate(rate=rate.rate, rating_name=rate.rating_name, review=review)
                rates_for_review.save()
                rate_payload.append(rates_for_review)
        final_data = model_to_dict(review, exclude=["id", "product", "customer"])
        final_data["uuid"] = review.uuid
        if rate_payload:
            final_data["rate"] = [model_to_dict(rate, exclude=["id", "review"]) for rate in rate_payload]

        review.send_to_magento()
        return Response(final_data)

    if request.method == "GET":
        return get(request, channel_idx, *args, **kwargs)
    else:
        return post(request, channel_idx, *args, **kwargs)


def _moderated_reviews(request, channel_idx: str):
    """A token pinned to a channel moderates that channel's reviews only; unpinned and legacy keys reach every review."""
    token = getattr(request, "access_token", None)
    if token is not None and token.channel_idx:
        return Review.objects.filter(channel_idx=channel_idx)
    return Review.objects.all()


@csrf_exempt
@authorize_api
@require_http_method("PATCH")
@parse_body(ReviewRequestPatch.Schema)
def modify_review(request, body: ReviewRequestPatch, channel_idx: str, uuid: str, *args, **kwargs):
    if not uuid:
        raise BadRequest("You need to specify the review UUID.")
    review = _moderated_reviews(request, channel_idx).filter(uuid=uuid).first()
    if not review:
        raise NotFound("There is no review with this UUID.")
    rate_payload = []
    with transaction.atomic():
        if body.sku:
            obj, created = ProductRepresentation.objects.get_or_create(
                sku=body.sku, defaults={"average_rate": 0, "number_of_reviews": 0}
            )
            review.product = obj

        if body.ratings:
            for rate in body.ratings:
                obj, is_created = Rate.objects.update_or_create(
                    review=review, rating_name=rate.rating_name, defaults={"rate": rate.rate}
                )
                rate_payload.append(obj)
            if OVERWRITE_RATES:
                Rate.objects.filter(review=review).exclude(pk__in=[obj.pk for obj in rate_payload]).delete()
        fields = ["title", "detail", "source", "status", "name"]
        for field in fields:
            if hasattr(body, field):
                value = getattr(body, field)
                if value is not None:
                    setattr(review, field, value)

        try:
            review.save()
        except Exception as e:
            logger.exception(e)
            raise BadRequest("Error while saving review.")

        final_data = model_to_dict(review, exclude=["id", "product", "customer"])
        final_data["uuid"] = review.uuid
        if rate_payload:
            final_data["rate"] = [model_to_dict(rate, exclude=["id", "review"]) for rate in rate_payload]
        return Response(final_data)
