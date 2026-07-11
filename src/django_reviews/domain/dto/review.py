# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import json
from dataclasses import field
from itertools import groupby
from typing import ClassVar

import marshmallow.validate
from marshmallow import Schema, fields, pre_load
from marshmallow_dataclass import add_schema, dataclass

from django_reviews.enum import ReviewType
from django_reviews.settings import (
    AVAILABLE_REVIEW_SOURCE,
    MAX_RATE,
    MAX_REVIEW_DETAIL_LENGTH,
    MAX_REVIEW_TITLE_LENGTH,
    RATINGS_NAME,
)


@dataclass
class Sorter:
    order: str
    Schema: ClassVar[type[Schema]] = Schema


@dataclass
class FieldSorter(Sorter):
    field: str
    Schema: ClassVar[type[Schema]] = Schema


@add_schema
@dataclass
class ReviewRatingsData:
    rate: float = field(metadata={"validate": marshmallow.validate.Range(max=MAX_RATE)})
    rating_name: str = field(metadata={"validate": marshmallow.validate.OneOf(RATINGS_NAME)})
    Schema: ClassVar[type[Schema]] = Schema


@add_schema
@dataclass
class ReviewRequest:
    sku: str
    title: str = field(metadata={"validate": marshmallow.validate.Length(max=MAX_REVIEW_TITLE_LENGTH)})
    detail: str = field(metadata={"validate": marshmallow.validate.Length(max=MAX_REVIEW_DETAIL_LENGTH)})
    ratings: list[ReviewRatingsData] = field(metadata={"validate": marshmallow.validate.Length(min=1)})
    source: str | None = field(metadata={"validate": marshmallow.validate.OneOf(AVAILABLE_REVIEW_SOURCE)})
    name: str | None
    Schema: ClassVar[type[Schema]] = Schema


@add_schema
@dataclass
class ReviewRequestPatch:
    sku: str | None
    name: str | None
    title: str | None = field(metadata={"validate": marshmallow.validate.Length(max=MAX_REVIEW_TITLE_LENGTH)})
    detail: str | None = field(metadata={"validate": marshmallow.validate.Length(max=MAX_REVIEW_DETAIL_LENGTH)})
    ratings: list[ReviewRatingsData] | None = field(metadata={"validate": marshmallow.validate.Length(min=1)})
    source: str | None = field(metadata={"validate": marshmallow.validate.OneOf(AVAILABLE_REVIEW_SOURCE)})
    status: str | None = field(
        metadata={"validate": marshmallow.validate.OneOf(choices=[status.value for status in ReviewType])}
    )
    Schema: ClassVar[type[Schema]] = Schema


@add_schema
@dataclass
class ReviewParams:
    sku: list[str]
    page: int
    limit: int
    sort: list[FieldSorter] | None = None
    source: str | None = None

    @pre_load
    def handle_sort(self, data, **kwargs):
        if "sort" in data:
            result = {**data}
            result["sort"] = [json.loads(elem) for elem in result.get("sort")]
            return result
        return data

    @pre_load
    def handle_parameter_list(self, data, **kwargs):
        """Aggregate values from list like parameters, for example from sku and sku[], into one field"""
        key_func = lambda x: x.strip("[]")
        grouped = groupby(sorted(data, key=key_func), key=key_func)
        result = {}
        for key, group in grouped:
            acc = []
            for elem in group:
                acc.extend(data.getlist(elem))

            field = self.declared_fields[key]
            if isinstance(field, fields.List):
                result[key] = acc
            else:
                result[key] = acc[0]
        return result


@add_schema
@dataclass
class ReviewDetailsResponse:
    rate: float
    rating_name: int


@add_schema
@dataclass
class ReviewResponse:
    name: str
    sku: str
    title: str
    detail: str
    created_at: str
    average_rate: float
    ratings: list[ReviewDetailsResponse]
    Schema: ClassVar[type[Schema]] = Schema
