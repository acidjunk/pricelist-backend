import datetime
import uuid
from operator import or_

import structlog
from server.apis.helpers import (
    delete,
    get_filter_from_args,
    get_range_from_args,
    get_sort_from_args,
    invalidateCompletedOrdersCache,
    invalidatePendingOrdersCache,
    load,
    query_with_filters,
    save,
    update,
)
from server.database import Order, Shop, ShopToPrice
from flask_login import current_user
from flask_restx import Namespace, Resource, abort, fields, marshal_with
from flask_security import roles_accepted
from sqlalchemy.orm import contains_eager, defer
from server.utils import is_ip_allowed
from flask import request
from server.allowed_ips import SHOPS_ALLOWED_IPS

logger = structlog.get_logger(__name__)

api = Namespace("orders", description="Order related operations")

order_info_marshaller = {
    "description": fields.String,
    "price": fields.Float,
    "kind_id": fields.String,
    "kind_name": fields.String,
    "product_id": fields.String,
    "product_name": fields.String,
    "internal_product_id": fields.String,
    "quantity": fields.Integer,
}

order_info_serializer = api.model(
    "OrderInfo",
    {
        "description": fields.String,
        "price": fields.Float,
        "kind_id": fields.String,
        "kind_name": fields.String,
        "product_id": fields.String,
        "product_name": fields.String,
        "internal_product_id": fields.String,
        "quantity": fields.Integer,
    },
)


order_serializer = api.model(
    "Order",
    {
        "id": fields.String(required=True),
        "shop_id": fields.String(required=True, description="Shop Id"),
        # Todo: use fields from improviser to marshall
        "order_info": fields.Nested(order_info_serializer),
        # "order_info": fields.String(),
        "total": fields.Float(required=True, description="Total"),
        "customer_order_id": fields.Integer,
    },
)

order_serializer_with_shop_names = {
    "id": fields.String(required=True),
    "shop_id": fields.String(required=True, description="Shop Id"),
    "shop_name": fields.String(description="Shop Name"),
    # Todo: use fields from improviser to marshall
    "order_info": fields.Nested(order_info_marshaller),
    # "order_info": fields.String(),
    "total": fields.Float(required=True, description="Total"),
    "customer_order_id": fields.Integer,
    "status": fields.String,
    "created_at": fields.DateTime,
    "completed_at": fields.DateTime,
    "completed_by": fields.String,
    "completed_by_name": fields.String,
    "table_id": fields.String,
    "table_name": fields.String,
}

order_response_marshaller = api.model(
    "ShortOrderResponse",
    {
        "id": fields.String,
        "customer_order_id": fields.Integer,
        "total": fields.Float,
        "status": fields.String,
        "created_at": fields.DateTime,
        "completed_at": fields.DateTime,
        "table_id": fields.String,
        "table_name": fields.String,
    },
)


parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")


def get_price_rules_total(order_items):
    """Calculate the total number of grams."""
    JOINT = 0.4

    # Todo: add correct order line for 0.5 and 2.5
    prices = {"0,5 gram": 0.5, "1 gram": 1, "2,5 gram": 2.5, "5 gram": 5, "joint": JOINT}
    total = 0
    for item in order_items:
        if item["description"] in prices:
            total = total + (prices[item["description"]] * item["quantity"])

    return total


def get_first_unavailable_product_name(order_items, shop_id):
    """Search for the first unavailable product and return it's name."""
    products = (
        ShopToPrice.query.join(ShopToPrice.price)
        .options(contains_eager(ShopToPrice.price), defer("price_id"))
        .filter(ShopToPrice.shop_id == shop_id)
        .all()
    )
    for item in order_items:
        found_product = False  # Start False
        for product in products:
            if item.get("kind_id") and item["kind_id"] == str(product.kind_id):
                if product.active:
                    if item["description"] == "0,5 gram" and (not product.use_half or not product.price.half):
                        logger.warning("Product is currently not available in 0.5 gram", kind_name=item["kind_name"])
                    elif item["description"] == "1 gram" and (not product.use_one or not product.price.one):
                        logger.warning("Product is currently not available in 1 gram", kind_name=item["kind_name"])
                    elif item["description"] == "2,5 gram" and (not product.use_two_five or not product.price.two_five):
                        logger.warning("Product is currently not available in 2.5 gram", kind_name=item["kind_name"])
                    elif item["description"] == "5 gram" and (not product.use_five or not product.price.five):
                        logger.warning("Product is currently not available in 5 gram", kind_name=item["kind_name"])
                    elif item["description"] == "1 joint" and (not product.use_joint or not product.price.joint):
                        logger.warning("Product is currently not available as joint", kind_name=item["kind_name"])
                    else:
                        logger.info(
                            "Found product in order item and in available products",
                            kind_id=item["kind_id"],
                            kind_name=item["kind_name"],
                        )
                        found_product = True
                else:
                    logger.warning("Product is currently not available", kind_name=item["kind_name"])
            if item.get("product_id") and item["product_id"] == str(product.product_id):
                if product.active:
                    if not product.use_piece or not product.price.piece:
                        logger.warning("Product is currently not available as piece", product_name=item["product_name"])
                    else:
                        logger.info(
                            "Found horeca product in order item and in available products",
                            product_id=item["product_id"],
                            product_name=item["product_name"],
                        )
                        found_product = True
                else:
                    logger.warning("Horeca product is currently not available", product_name=item["product_name"])
        if not found_product:
            return item["kind_name"] if item["kind_name"] else item["product_name"]
    return None


@api.route("/")
@api.doc("Show all orders.")
class OrderResourceList(Resource):

    # @roles_accepted("admin")
    @marshal_with(order_serializer_with_shop_names)
    @api.doc(parser=parser)
    def get(self):
        """List Orders"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args, "created_at", default_sort_order="DESC")
        filter = get_filter_from_args(args)

        query_result, content_range = query_with_filters(Order, Order.query, range, sort, filter)
        for order in query_result:
            if (order.status == "complete" or order.status == "cancelled") and order.completed_by:
                order.completed_by_name = order.user.first_name
            if order.table_id:
                order.table_name = order.table.name

        return query_result, 200, {"Content-Range": content_range}

    @api.expect(order_serializer)
    @api.marshal_with(order_response_marshaller)
    def post(self):
        """New Order"""
        print(request.__dict__)
        payload = api.payload
        if payload.get("customer_order_id"):
            del payload["customer_order_id"]
        shop_id = payload.get("shop_id")
        if not shop_id:
            abort(400, "shop_id not in payload")
            pass
        if not is_ip_allowed(request, SHOPS_ALLOWED_IPS, shop_id):
            abort(400, "Your IP is not allowed!")

        # 5 gram checks
        total_cannabis = get_price_rules_total(payload["order_info"])
        logger.info("Checked order weight", weight=total_cannabis)
        if total_cannabis > 5:
            abort(400, "MAX_5_GRAMS_ALLOWED")

        # Availability check
        unavailable_product_name = get_first_unavailable_product_name(payload["order_info"], shop_id)
        if unavailable_product_name:
            abort(400, f"{unavailable_product_name}, OUT_OF_STOCK")

        shop = load(Shop, str(shop_id))  # also handles 404 when shop can't be found
        payload["customer_order_id"] = Order.query.filter_by(shop_id=str(shop.id)).count() + 1
        # Todo: recalculate total and use it as a checksum for the payload
        order_id = str(uuid.uuid4())
        order = Order(id=order_id, **payload)
        save(order)
        invalidatePendingOrdersCache(order_id)
        return order, 201


@api.route("/<id>")
@api.doc("Order detail operations.")
class OrderResource(Resource):
    # @roles_accepted("admin", "employee")
    @marshal_with(order_serializer_with_shop_names)
    def get(self, id):
        """List Order"""
        item = load(Order, id)
        item.shop_name = item.shop.name
        return item, 200

    # @roles_accepted("admin", "employee")
    @api.expect(order_serializer)
    @api.marshal_with(order_serializer)
    def put(self, id):
        """Edit Order"""
        item = load(Order, id)
        if (
            api.payload.get("status")
            and (api.payload["status"] == "completed" or api.payload["status"] == "cancelled")
            and not item.completed_at
        ):
            item.completed_at = datetime.datetime.utcnow()
            item.completed_by = current_user.id
        item = update(item, api.payload)
        return item, 201

    # @roles_accepted("admin")
    def delete(self, id):
        """Delete Order"""
        item = load(Order, id)
        delete(item)
        return "", 204

    # @roles_accepted("admin", "employee")
    @api.expect(order_serializer)
    def patch(self, id):
        item = load(Order, id)
        if (
            "complete" not in item.status
            and api.payload.get("status")
            and (api.payload["status"] == "complete" or api.payload["status"] == "cancelled")
            and not item.completed_at
        ):
            item.completed_at = datetime.datetime.utcnow()
            item.completed_by = current_user.id
        _ = update(item, api.payload)
        invalidateCompletedOrdersCache(item.id)
        return "", 204


@api.route("/shop/<shop_id>/pending")
@api.doc("Show all pending orders per shop.")
class PendingOrderResourceList(Resource):
    @roles_accepted("admin")
    @marshal_with(order_serializer_with_shop_names)
    @api.doc(parser=parser)
    def get(self, shop_id):
        """List Orders"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args, "created_at", default_sort_order="DESC")
        filter = get_filter_from_args(args)

        query = Order.query.filter(Order.shop_id == shop_id).filter(Order.status == "pending")
        query_result, content_range = query_with_filters(Order, query, range, sort, filter)
        for order in query_result:
            if order.table_id:
                order.table_name = order.table.name

        return query_result, 200, {"Content-Range": content_range}


@api.route("/shop/<shop_id>/complete")
@api.doc("Show all complete orders per shop.")
class CompletedOrderResourceList(Resource):
    @roles_accepted("admin")
    @marshal_with(order_serializer_with_shop_names)
    @api.doc(parser=parser)
    def get(self, shop_id):
        """List Orders"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args, "created_at", default_sort_order="DESC")
        filter = get_filter_from_args(args)

        query = Order.query.filter(Order.shop_id == shop_id).filter(or_(Order.status == "complete", Order.status == "cancelled"))
        query_result, content_range = query_with_filters(Order, query, range, sort, filter)
        for order in query_result:
            if (order.status == "complete" or order.status == "cancelled") and order.completed_by:
                order.completed_by_name = order.user.first_name
            if order.table_id:
                order.table_name = order.table.name

        return query_result, 200, {"Content-Range": content_range}


@api.route("/check/<ids>")
@api.doc("Check order details.")
class OrderResource(Resource):
    @marshal_with(order_response_marshaller)
    def get(self, ids):
        """List Order"""
        id_list = ids.split(",")

        # Validate input
        for index, id in enumerate(id_list):
            if not validate_uuid4(id):
                abort(400, f"ID {index+1} is not valid")

        if len(id_list) > 10:
            abort(400, "Max 10 orders")

        # Build response
        items = []
        for id in id_list:
            item = load(Order, id, allow_404=True)
            if item:
                item.table_name = item.table.name
                items.append(item)

        for item in items:
            if item.shop_id != items[0].shop_id:
                abort(400, "All ID's should belong to one shop")

        return items, 200
