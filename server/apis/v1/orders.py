import datetime
import uuid

import structlog
from apis.helpers import (
    delete,
    get_filter_from_args,
    get_range_from_args,
    get_sort_from_args,
    load,
    query_with_filters,
    save,
    update,
)
from database import Order, Shop
from flask_restx import Namespace, Resource, abort, fields, marshal_with
from flask_security import roles_accepted

logger = structlog.get_logger(__name__)

api = Namespace("orders", description="Order related operations")

order_info_marshaller = {
    "description": fields.String,
    "price": fields.Float,
    "kind_id": fields.Integer,
    "kind_name": fields.Integer,
    "internal_product_id": fields.String,
    "quantity": fields.Integer,
}

order_serializer = api.model(
    "Order",
    {
        "id": fields.String(required=True),
        "shop_id": fields.String(required=True, description="Shop Id"),
        # Todo: use fields from improviser to marshall
        "order_info": fields.Nested(order_info_marshaller),
        # "order_info": fields.String(),
        "total": fields.Float(required=True, description="Total"),
    },
)

order_serializer_with_shop_names = {
    "id": fields.String(required=True),
    "shop_id": fields.String(required=True, description="Shop Id"),
    "shop_name": fields.String(description="Shop Name"),
    # Todo: use fields from improviser to marshall
    "order_info": fields.Nested(order_info_marshaller),
    # "order_info": fields.String(),
    "total": fields.String(required=True, description="Total"),
}

order_response_marshaller = {"id": fields.String, "customer_order_id": fields.Integer, "total": fields.Float}


parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")


@api.route("/")
@api.doc("Show all categories.")
class OrderResourceList(Resource):
    @roles_accepted("admin")
    @marshal_with(order_serializer_with_shop_names)
    @api.doc(parser=parser)
    def get(self):
        """List Orders"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args, "created_at", default_sort_order="DESC")
        filter = get_filter_from_args(args)

        query_result, content_range = query_with_filters(Order, Order.query, range, sort, filter)

        return query_result, 200, {"Content-Range": content_range}

    @api.expect(order_serializer)
    @api.marshal_with(order_response_marshaller)
    def post(self):
        """New Order"""
        payload = api.payload
        shop_id = payload.get("shop_id")
        if not shop_id:
            abort(400, "shop_id not in payload")

        shop = load(Shop, str(shop_id))
        if not shop:
            return {}, 600
        payload["customer_order_id"] = Order.query.filter_by(shop_id=str(shop.id)).count() + 1
        # Todo: recalculate total and use it as a checksum for the payload
        order = Order(id=str(uuid.uuid4()), **payload)
        save(order)
        return order, 201


@api.route("/<id>")
@api.doc("Order detail operations.")
class OrderResource(Resource):
    @roles_accepted("admin", "employee")
    @marshal_with(order_serializer_with_shop_names)
    def get(self, id):
        """List Order"""
        item = load(Order, id)
        item.shop_name = item.shop.name
        return item, 200

    @roles_accepted("admin", "employee")
    @api.expect(order_serializer)
    @api.marshal_with(order_serializer)
    def put(self, id):
        """Edit Order"""
        item = load(Order, id)
        if api.payload.get("status") and api.payload["status"] == "completed" and not item.completed_at:
            item.completed_at = datetime.datetime.utcnow()
        item = update(item, api.payload)
        return item, 201

    @roles_accepted("admin")
    def delete(self, id):
        """Delete Order"""
        item = load(Order, id)
        delete(item)
        return "", 204

    @api.expect(order_serializer)
    def patch(self, id):
        item = load(Order, id)
        if (
            "complete" not in item.status
            and api.payload.get("status")
            and api.payload["status"] == "complete"
            and not item.completed_at
        ):
            item.completed_at = datetime.datetime.utcnow()
        _ = update(item, api.payload)
        return "", 204
