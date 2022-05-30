import uuid

import structlog
from server.apis.helpers import (
    delete,
    get_filter_from_args,
    get_range_from_args,
    get_sort_from_args,
    load,
    query_with_filters,
    save,
    update,
)
from server.database import Price
from flask_restx import Namespace, Resource, fields, marshal_with
from flask_security import roles_accepted

logger = structlog.get_logger(__name__)

api = Namespace("prices", description="Prices related operations")

tag_fields = {"id": fields.String, "name": fields.String, "amount": fields.Integer}
flavor_fields = {"id": fields.String, "name": fields.String, "icon": fields.String, "color": fields.String}

price_serializer = api.model(
    "Price",
    {
        "id": fields.String(),
        "internal_product_id": fields.String(required=True, description="POS ID"),
        "half": fields.Float(description="Price for half gram"),
        "one": fields.Float(description="Price for one gram"),
        "two_five": fields.Float(description="Price for two and a half gram"),
        "five": fields.Float(description="Price for five gram"),
        "joint": fields.Float(description="Price for one joint"),
        "piece": fields.Float(description="Price for one item"),
    },
)

parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")


@api.route("/")
@api.doc("Show all prices.")
class PriceResourceList(Resource):
    @roles_accepted("admin")
    @marshal_with(price_serializer)
    @api.doc(parser=parser)
    def get(self):
        """List (Product)Prices"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args, "internal_product_id")
        filter = get_filter_from_args(args)

        query_result, content_range = query_with_filters(
            Price, Price.query, range, sort, filter, quick_search_columns=["internal_product_id"]
        )
        return query_result, 200, {"Content-Range": content_range}

    @roles_accepted("admin")
    @api.expect(price_serializer)
    @api.marshal_with(price_serializer)
    def post(self):
        """New Prices"""
        price = Price(id=str(uuid.uuid4()), **api.payload)
        save(price)
        return price, 201


@api.route("/<id>")
@api.doc("Price detail operations.")
class PriceResource(Resource):
    @marshal_with(price_serializer)
    def get(self, id):
        """List Price"""
        item = load(Price, id)
        return item, 200

    @roles_accepted("admin")
    @api.expect(price_serializer)
    @api.marshal_with(price_serializer)
    def put(self, id):
        """Edit Price"""
        item = load(Price, id)
        item = update(item, api.payload)
        return item, 201

    @roles_accepted("admin")
    def delete(self, id):
        """Delete Price"""
        item = load(Price, id)
        delete(item)
        return "", 204
