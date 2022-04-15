import uuid
from datetime import datetime

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
from database import Product
from flask_restx import Namespace, Resource, fields, marshal_with
from flask_security import roles_accepted

logger = structlog.get_logger(__name__)

api = Namespace("products", description="Product related operations")

tag_fields = {"id": fields.String, "name": fields.String, "amount": fields.Integer}
flavor_fields = {"id": fields.String, "name": fields.String, "icon": fields.String, "color": fields.String}

product_serializer = api.model(
    "Product",
    {
        "id": fields.String(),
        "name": fields.String(required=True, description="Product name"),
        "short_description_nl": fields.String(description="NL Description as shown in the price list"),
        "description_nl": fields.String(description="EN Description as shown in the detail view"),
        "short_description_en": fields.String(description="NL Description as shown in the price list"),
        "description_en": fields.String(description="EN Description as shown in the detail view"),
        "approved": fields.Boolean(description="Approved?"),
    },
)

price_fields = {
    "id": fields.String,
    "internal_product_id": fields.String,
    "active": fields.Boolean,
    "new": fields.Boolean,
    "one": fields.Float,
    "two_five": fields.Float,
    "five": fields.Float,
    "joint": fields.Float,
    "piece": fields.Float,
    "created_at": fields.DateTime,
    "modified_at": fields.DateTime,
}

product_serializer_with_relations = {
    "id": fields.String(),
    "name": fields.String(required=True, description="Product name"),
    "short_description_nl": fields.String(description="NL Description as shown in the price list"),
    "description_nl": fields.String(description="EN Description as shown in the detail view"),
    "short_description_en": fields.String(description="NL Description as shown in the price list"),
    "description_en": fields.String(description="EN Description as shown in the detail view"),
    "images_amount": fields.Integer("Number of images"),
    "image_1": fields.String(required=True, description="File Name 1"),
    "image_2": fields.String(required=True, description="File Name 2"),
    "image_3": fields.String(required=True, description="File Name 3"),
    "image_4": fields.String(required=True, description="File Name 4"),
    "image_5": fields.String(required=True, description="File Name 5"),
    "image_6": fields.String(required=True, description="File Name 6"),
    "complete": fields.Boolean(description="Complete?"),
    "created_at": fields.DateTime(description="Creation date"),
    "modified_at": fields.DateTime(description="Last modification date"),
    "approved_at": fields.DateTime(description="Ready for sale date"),
    "prices": fields.Nested(price_fields),
}


parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")


@api.route("/")
@api.doc("Show all products.")
class ProductResourceList(Resource):
    @marshal_with(product_serializer_with_relations)
    @api.doc(parser=parser)
    def get(self):
        """List Products"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args)
        filter = get_filter_from_args(args)

        query_result, content_range = query_with_filters(
            Product,
            Product.query,
            range,
            sort,
            filter,
            quick_search_columns=["name", "short_description_nl", "short_description_en"],
        )

        for product in query_result:
            product.images_amount = 0
            for i in [1, 2, 3, 4, 5, 6]:
                if getattr(product, f"image_{i}"):
                    product.images_amount += 1

        return query_result, 200, {"Content-Range": content_range}

    @roles_accepted("admin")
    @api.expect(product_serializer)
    @api.marshal_with(product_serializer)
    def post(self):
        """New Shops"""
        product = Product(id=str(uuid.uuid4()), **api.payload)
        save(product)
        return product, 201


detail_parser = api.parser()
detail_parser.add_argument("shop", location="args", help="Optional shop id")


@api.route("/<id>")
@api.doc("Product detail operations.")
class ProductResource(Resource):
    @marshal_with(product_serializer_with_relations)
    @api.doc(parser=detail_parser)
    def get(self, id):
        """List Product"""
        args = detail_parser.parse_args()

        item = load(Product, id)

        shop = args.get("shop")
        if shop:
            item.prices = []
            for price_relation in item.shop_to_price:
                if str(price_relation.shop_id) == shop:
                    item.prices.append(
                        {
                            "id": price_relation.price.id,
                            "internal_product_id": price_relation.price.internal_product_id,
                            "active": price_relation.active,
                            "new": price_relation.new,
                            "half": price_relation.price.half if price_relation.use_half else None,
                            "one": price_relation.price.one if price_relation.use_one else None,
                            "two_five": price_relation.price.two_five if price_relation.use_two_five else None,
                            "five": price_relation.price.five if price_relation.use_five else None,
                            "joint": price_relation.price.joint if price_relation.use_joint else None,
                            "piece": price_relation.price.piece if price_relation.use_piece else None,
                            "created_at": price_relation.created_at,
                            "modified_at": price_relation.modified_at,
                        }
                    )
        else:
            item.prices = []

        item.images_amount = 0
        for i in [1, 2, 3, 4, 5, 6]:
            if getattr(item, f"image_{i}"):
                item.images_amount += 1

        return item, 200

    @roles_accepted("admin")
    @api.expect(product_serializer)
    @api.marshal_with(product_serializer)
    def put(self, id):
        """Edit Product"""
        item = load(Product, id)
        if api.payload.get("approved"):
            if api.payload["approved"] and not item.approved:
                api.payload["approved_at"] = datetime.utcnow()
            if not api.payload["approved"] and item.approved:
                api.payload["approved_at"] = None

        api.payload["complete"] = (
            True if item.image_1 and api.payload.get("description_nl") and api.payload.get("description_en") else False
        )

        item = update(item, api.payload)
        return item, 201

    @roles_accepted("admin")
    def delete(self, id):
        """Product Delete """
        item = load(Product, id)
        delete(item)
        return "", 204
