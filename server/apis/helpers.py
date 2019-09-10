from typing import List

import structlog
from more_itertools import chunked
from sqlalchemy import String, cast
from sqlalchemy.sql import expression

logger = structlog.get_logger(__name__)


def get_range_from_args(args):
    if args["range"]:
        range = []
        try:
            input = args["range"][1:-1].split(",")
            for i in input:
                range.append(int(i))
            logger.info("Query parameters set to custom range", range=range)
            return range
        except:  # noqa: E722
            logger.warning("Query parameters not parsable", args=args.get(["range"], "No range provided"))
    range = [0, 19]  # Default range
    logger.info("Query parameters set to default range", range=range)
    return range


def get_sort_from_args(args, default_sort="name"):
    sort = []
    if args["sort"]:
        try:
            input = args["sort"].split(",")
            sort.append(input[0][2:-1])
            sort.append(input[1][1:-2])
            logger.info("Query parameters set to custom sort", sort=sort)
            return sort
        except:  # noqa: E722
            logger.warning("Query parameters not parsable", args=args.get(["sort"], "No sort provided"))
        return range
    sort = [default_sort, "ASC"]  # Default sort
    logger.info("Query parameters set to default sort", sort=sort)
    return sort


def query_with_filters(model, query, range: List[int] = None, sort: List[str] = None, filters: List[str] = None):
    if filters is not None:
        for filter in chunked(filters, 2):
            if filter and len(filter) == 2:
                field = filter[0]
                value = filter[1]
                # Todo Make filter better Field aware
                value_as_bool = value in ("Yes", "Y", "y", "True", "TRUE", "true")  # noqa: F841
                if value is not None:
                    if field.endswith("_gt"):
                        query = query.filter(model.__dict__[field[:-3]] > value)
                    elif field.endswith("_gte"):
                        query = query.filter(model.__dict__[field[:-4]] >= value)
                    elif field.endswith("_lte"):
                        query = query.filter(model.__dict__[field[:-4]] <= value)
                    elif field.endswith("_lt"):
                        query = query.filter(model.__dict__[field[:-3]] < value)
                    elif field.endswith("_ne"):
                        query = query.filter(model.__dict__[field[:-3]] != value)
                    else:
                        query = query.filter(cast(model.__dict__[field], String).ilike("%" + value + "%"))

    if sort and len(sort) == 2:
        if sort[1].upper() == "DESC":
            query = query.order_by(expression.desc(model.__dict__[sort[0]]))
        else:
            query = query.order_by(expression.asc(model.__dict__[sort[0]]))

    range_start = int(range[0])
    range_end = int(range[1])
    # Range is inclusive so we need to add one
    if len(range) >= 2:
        # Range is inclusive so we need to add one
        range_length = max(range_end - range_start + 1, 0)
        query = query.offset(range_start)
        query = query.limit(range_length)
    total = query.count()

    content_range = f"kinds {range_start}-{range_end}/{total}"

    return query.all(), content_range
