from http import HTTPStatus
from typing import Dict, List, Tuple

import structlog
from database import Flavor, Tag, User
from more_itertools import chunked
from sqlalchemy import String, cast, func
from sqlalchemy.sql import expression

logger = structlog.get_logger(__name__)


def _flavor_query_with_filters(query, range: List[int] = None, sort: List[str] = None, filters: List[str] = None):
    if filters is not None:
        for filter in chunked(filters, 2):
            if filter and len(filter) == 2:
                field = filter[0]
                value = filter[1]
                value_as_bool = value in ("Yes", "Y", "y", "True", "TRUE", "true")
                if value is not None:
                    if field.endswith("_gt"):
                        query = query.filter(Flavor.__dict__[field[:-3]] > value)
                    elif field.endswith("_gte"):
                        query = query.filter(Flavor.__dict__[field[:-4]] >= value)
                    elif field.endswith("_lte"):
                        query = query.filter(Flavor.__dict__[field[:-4]] <= value)
                    elif field.endswith("_lt"):
                        query = query.filter(Flavor.__dict__[field[:-3]] < value)
                    elif field.endswith("_ne"):
                        query = query.filter(Flavor.__dict__[field[:-3]] != value)
                    else:
                        query = query.filter(cast(Flavor.__dict__[field], String).ilike("%" + value + "%"))

    if sort and len(sort) == 2:
        if sort[1].upper() == "DESC":
            query = query.order_by(expression.desc(Flavor.__dict__[sort[0]]))
        else:
            query = query.order_by(expression.asc(Flavor.__dict__[sort[0]]))

    range_start = int(range[0])
    range_end = int(range[1])
    # Range is inclusive so we need to add one
    if len(range) >= 2:
        # Range is inclusive so we need to add one
        range_length = max(range_end - range_start + 1, 0)
        query = query.offset(range_start)
        query = query.limit(range_length)
    total = query.count()

    content_range = f"flavors {range_start}-{range_end}/{total}"

    return query.all(), content_range


def _tag_query_with_filters(query, range: List[int] = None, sort: List[str] = None, filters: List[str] = None):
    if filters is not None:
        for filter in chunked(filters, 2):
            if filter and len(filter) == 2:
                field = filter[0]
                value = filter[1]
                value_as_bool = value in ("Yes", "Y", "y", "True", "TRUE", "true")
                if value is not None:
                    if field.endswith("_gt"):
                        query = query.filter(Tag.__dict__[field[:-3]] > value)
                    elif field.endswith("_gte"):
                        query = query.filter(Tag.__dict__[field[:-4]] >= value)
                    elif field.endswith("_lte"):
                        query = query.filter(Tag.__dict__[field[:-4]] <= value)
                    elif field.endswith("_lt"):
                        query = query.filter(Tag.__dict__[field[:-3]] < value)
                    elif field.endswith("_ne"):
                        query = query.filter(Tag.__dict__[field[:-3]] != value)
                    else:
                        query = query.filter(cast(Tag.__dict__[field], String).ilike("%" + value + "%"))

    if sort and len(sort) == 2:
        if sort[1].upper() == "DESC":
            query = query.order_by(expression.desc(Tag.__dict__[sort[0]]))
        else:
            query = query.order_by(expression.asc(Tag.__dict__[sort[0]]))

    range_start = int(range[0])
    range_end = int(range[1])
    # Range is inclusive so we need to add one
    if len(range) >= 2:
        # Range is inclusive so we need to add one
        range_length = max(range_end - range_start + 1, 0)
        query = query.offset(range_start)
        query = query.limit(range_length)
    total = query.count()

    content_range = f"tags {range_start}-{range_end}/{total}"

    return query.all(), content_range


def _user_query_with_filters(query, range: List[int] = None, sort: List[str] = None, filters: List[str] = None):
    if filters is not None:
        for filter in chunked(filters, 2):
            if filter and len(filter) == 2:
                field = filter[0]
                value = filter[1]
                value_as_bool = value in ("Yes", "Y", "y", "True", "TRUE", "true")
                if value is not None:
                    if field.endswith("_gt"):
                        query = query.filter(User.__dict__[field[:-3]] > value)
                    elif field.endswith("_gte"):
                        query = query.filter(User.__dict__[field[:-4]] >= value)
                    elif field.endswith("_lte"):
                        query = query.filter(User.__dict__[field[:-4]] <= value)
                    elif field.endswith("_lt"):
                        query = query.filter(User.__dict__[field[:-3]] < value)
                    elif field.endswith("_ne"):
                        query = query.filter(User.__dict__[field[:-3]] != value)
                    else:
                        query = query.filter(cast(User.__dict__[field], String).ilike("%" + value + "%"))

    if sort and len(sort) == 2:
        if sort[1].upper() == "DESC":
            query = query.order_by(expression.desc(User.__dict__[sort[0]]))
        else:
            query = query.order_by(expression.asc(User.__dict__[sort[0]]))

    range_start = int(range[0])
    range_end = int(range[1])
    # Range is inclusive so we need to add one
    if len(range) >= 2:
        # Range is inclusive so we need to add one
        range_length = max(range_end - range_start + 1, 0)
        query = query.offset(range_start)
        query = query.limit(range_length)
    total = query.count()

    content_range = f"users {range_start}-{range_end}/{total}"

    return query.all(), content_range
