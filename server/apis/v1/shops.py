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
from database import Category, Price, Shop, ShopToPrice
from flask_restx import Namespace, Resource, fields, marshal_with
from flask_security import roles_accepted

logger = structlog.get_logger(__name__)

api = Namespace("shops", description="Shop related operations")

strain_fields = {"name": fields.String}


price_fields = {
    "id": fields.String,
    "internal_product_id": fields.Integer,
    "active": fields.Boolean,
    "category_id": fields.String,
    "category_name": fields.String,
    "kind_id": fields.String,
    "kind_image": fields.String,
    "kind_strains": fields.Nested(strain_fields),
    "kind_name": fields.String,
    "kind_short_description_nl": fields.String,
    "kind_short_description_en": fields.String,
    "product_id": fields.String,
    "product_image": fields.String,
    "product_name": fields.String,
    "product_short_description_nl": fields.String,
    "product_short_description_en": fields.String,
    "kind_c": fields.Boolean,
    "kind_h": fields.Boolean,
    "kind_i": fields.Boolean,
    "kind_s": fields.Boolean,
    "half": fields.Float,
    "one": fields.Float,
    "two_five": fields.Float,
    "five": fields.Float,
    "joint": fields.Float,
    "piece": fields.Float,
}

shop_serializer = api.model(
    "Shop",
    {
        "id": fields.String(),
        "name": fields.String(required=True, description="Unique Shop"),
        "description": fields.String(required=True, description="Shop description", default=False),
    },
)

shop_serializer_with_prices = {
    "id": fields.String(),
    "name": fields.String(required=True, description="Unique Shop"),
    "description": fields.String(required=True, description="Shop description", default=False),
    "prices": fields.Nested(price_fields),
}

shop_hash_fields = {
    "modified_at": fields.Datetime()
}

parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")


@api.route("/")
@api.doc("Show all shops.")
class ShopResourceList(Resource):
    @marshal_with(shop_serializer)
    def get(self):
        """List Shops"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args)
        filter = get_filter_from_args(args)

        query_result, content_range = query_with_filters(Shop, Shop.query, range, sort, filter)
        return query_result, 200, {"Content-Range": content_range}

    @roles_accepted("admin")
    @api.expect(shop_serializer)
    @api.marshal_with(shop_serializer)
    def post(self):
        """New Shops"""
        shop = Shop(id=str(uuid.uuid4()), **api.payload)
        save(shop)
        return shop, 201

@api.route("/cache-status/<id>")
@api.doc("Shop cache status so clients can determine if the cash should be invalidated.")
class ShopCacheResource(Resource):
    @marshal_with(shop_hash_fields)
    def get(self, id):
        """Show date of last change in data that could be visible in this shop"""
        item = load(Shop, id)
        return item, 200


@api.route("/<id>")
@api.doc("Shop detail operations.")
class ShopResource(Resource):
    @marshal_with(shop_serializer_with_prices)
    def get(self, id):
        """List Shop"""
        item = load(Shop, id)
        price_relations = (
            ShopToPrice.query.filter_by(shop_id=item.id)
            .join(ShopToPrice.price)
            .join(ShopToPrice.category)
            .order_by(Category.name, Price.internal_product_id)
            .all()
        )
        item.prices = [
            {
                "id": pr.id,
                "internal_product_id": pr.price.internal_product_id,
                "active": pr.active,
                "category_id": pr.category_id,
                "category_name": pr.category.name,
                "kind_id": pr.kind_id,
                "kind_image": pr.kind.image_1 if pr.kind_id else None,
                "kind_name": pr.kind.name if pr.kind_id else None,
                "kind_strains": [strain.strain for strain in pr.kind.kind_to_strains] if pr.kind_id else [],
                "kind_short_description_nl": pr.kind.short_description_nl if pr.kind_id else None,
                "kind_short_description_en": pr.kind.short_description_en if pr.kind_id else None,
                "kind_c": pr.kind.c if pr.kind_id else None,
                "kind_h": pr.kind.h if pr.kind_id else None,
                "kind_i": pr.kind.i if pr.kind_id else None,
                "kind_s": pr.kind.s if pr.kind_id else None,
                "product_id": pr.product_id,
                "product_image": pr.product.image_1 if pr.product_id else None,
                "product_name": pr.product.name if pr.product_id else None,
                "product_short_description_nl": pr.product.short_description_nl if pr.product_id else None,
                "product_short_description_en": pr.product.short_description_en if pr.product_id else None,
                "half": pr.price.half if pr.use_half else None,
                "one": pr.price.one if pr.use_one else None,
                "two_five": pr.price.two_five if pr.use_two_five else None,
                "five": pr.price.five if pr.use_five else None,
                "joint": pr.price.joint if pr.use_joint else None,
                "piece": pr.price.piece if pr.use_piece else None,
            }
            for pr in price_relations
        ]
        return item, 200

    @roles_accepted("admin")
    @api.expect(shop_serializer)
    @api.marshal_with(shop_serializer)
    def put(self, id):
        """Edit Shop"""
        item = load(Shop, id)
        item = update(item, api.payload)
        return item, 201

    @roles_accepted("admin")
    def delete(self, id):
        """Delete Shop"""
        item = load(Shop, id)
        delete(item)
        return "", 204
