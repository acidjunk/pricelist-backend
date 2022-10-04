import uuid

from apis.helpers import (
    delete,
    get_filter_from_args,
    get_range_from_args,
    get_sort_from_args,
    invalidateShopCache,
    load,
    query_with_filters,
    save,
    update,
)
from database import Category, Kind, Price, Product, Shop, ShopToPrice, db
from flask_restx import Namespace, Resource, abort, fields, marshal_with
from flask_security import roles_accepted
from sqlalchemy.orm import contains_eager, defer

api = Namespace("shops-to-prices", description="Shop to price related operations")

shop_to_price_serializer = api.model(
    "ShopToPrice",
    {
        "id": fields.String(),
        "active": fields.Boolean(default=True),
        "new": fields.Boolean(default=False),
        "price_id": fields.String(required=True, description="Price Id"),
        "shop_id": fields.String(required=True, description="Shop Id"),
        "category_id": fields.String(description="Category Id"),
        "kind_id": fields.String(required=True, description="Kind Id"),
        "product_id": fields.String(required=True, description="Product Id"),
        "use_half": fields.Boolean(default=True, description="Use the price for 0.5g?"),
        "use_one": fields.Boolean(default=True, description="Use the price for 1?"),
        "use_two_five": fields.Boolean(default=True, description="Use the price for 2.5g?"),
        "use_five": fields.Boolean(default=True, description="Use the price for 5g?"),
        "use_joint": fields.Boolean(default=True, description="Use the price for joint?"),
        "use_piece": fields.Boolean(default=True, description="Use the price for piece?"),
        "grams_joint": fields.Float(default=0),
        "grams_piece": fields.Float(default=0),
    },
)

shop_to_price_serializer_with_prices = {
    "id": fields.String(),
    "active": fields.Boolean(default=True),
    "new": fields.Boolean(default=False),
    "price_id": fields.String(required=True, description="Price Id"),
    "shop_id": fields.String(required=True, description="Shop Id"),
    "category_id": fields.String(description="Category Id"),
    "kind_id": fields.String(required=True, description="Kind Id"),
    "product_id": fields.String(required=True, description="Product Id"),
    "use_half": fields.Boolean(default=True, description="Show the price for 0.5g?"),
    "half": fields.Float(description="Price for half gram"),
    "use_one": fields.Boolean(default=True, description="Show the price for 1?"),
    "one": fields.Float(description="Price for one gram"),
    "use_two_five": fields.Boolean(default=True, description="Show the price for 2.5g?"),
    "two_five": fields.Float(description="Price for two and a half gram"),
    "use_five": fields.Boolean(default=True, description="Show the price for 5g?"),
    "five": fields.Float(description="Price for five gram"),
    "use_joint": fields.Boolean(default=True, description="Show the price for joint?"),
    "joint": fields.Float(description="Price for one joint"),
    "use_piece": fields.Boolean(default=True, description="Show the price for one piece?"),
    "piece": fields.Float(description="Price for one item"),
    "grams_joint": fields.Float(default=0),
    "grams_piece": fields.Float(default=0),
    "created_at": fields.DateTime(description="Creation date"),
    "modified_at": fields.DateTime(description="Last modification date"),
}

shop_to_price_availability_serializer = api.model(
    "ShopToPriceAvailability",
    {"active": fields.Boolean(required=True, description="Whether a Shop to Price relation is in stock.")},
)


parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")


@api.route("/")
@api.doc("ShopsToPrices")
class ShopsToPricesResourceList(Resource):
    @marshal_with(shop_to_price_serializer_with_prices)
    @api.doc(parser=parser)
    def get(self):
        """List prices for a shop"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args, "id")
        filter = get_filter_from_args(args)

        query = ShopToPrice.query.join(ShopToPrice.price).options(contains_eager(ShopToPrice.price), defer("price_id"))

        query_result, content_range = query_with_filters(ShopToPrice, query, range, sort, filter)

        for result in query_result:
            result.half = result.price.half if result.price.half and result.use_half else None
            result.one = result.price.one if result.price.one and result.use_one else None
            result.two_five = result.price.two_five if result.price.two_five and result.use_two_five else None
            result.five = result.price.five if result.price.five and result.use_five else None
            result.joint = result.price.joint if result.price.joint and result.use_joint else None
            result.piece = result.price.piece if result.price.piece and result.use_piece else None

        return query_result, 200, {"Content-Range": content_range}

    @roles_accepted("admin")
    @api.expect(shop_to_price_serializer)
    @api.marshal_with(shop_to_price_serializer)
    def post(self):
        """Add new price rules to Shops"""
        price = Price.query.filter(Price.id == api.payload["price_id"]).first()
        shop = Shop.query.filter(Shop.id == api.payload["shop_id"]).first()
        kind = Kind.query.filter(Kind.id == api.payload["kind_id"]).first() if api.payload.get("kind_id") else None
        product = (
            Product.query.filter(Product.id == api.payload["product_id"]).first()
            if api.payload.get("product_id")
            else None
        )
        category = None
        if api.payload.get("category_id"):
            category = Category.query.filter(Category.id == api.payload["category_id"]).first()

        if not price or not shop:
            abort(400, "Price or Shop not found")

        if (product and kind) or not product and not kind:
            abort(400, "One Cannabis or one Horeca product has to be provided")

        order_number = 0
        if kind:
            check_query = (
                ShopToPrice.query.filter_by(shop_id=shop.id)
                .filter_by(price_id=price.id)
                .filter_by(kind_id=kind.id)
                .all()
            )
            if len(check_query) > 0:
                abort(409, "Relation already exists")

        if product:
            check_query = (
                ShopToPrice.query.filter_by(shop_id=shop.id)
                .filter_by(price_id=price.id)
                .filter_by(product_id=product.id)
                .all()
            )
            if len(check_query) > 0:
                abort(409, "Relation already exists")
            amount_of_products = ShopToPrice.query.filter_by(shop_id=shop.id).filter_by(category_id=category.id).count()
            order_number = amount_of_products + 1

        data = api.payload
        shop_to_price = ShopToPrice(
            id=str(uuid.uuid4()),
            active=data["active"] if data.get("active") else False,
            new=data["new"] if data.get("new") else False,
            kind=kind,
            product=product,
            category=category,
            shop=shop,
            price=price,
            use_half=data["use_half"] if data.get("use_half") else False,
            use_one=data["use_one"] if data.get("use_one") else False,
            use_two_five=data["use_two_five"] if data.get("use_two_five") else False,
            use_five=data["use_five"] if data.get("use_five") else False,
            use_joint=data["use_joint"] if data.get("use_joint") else False,
            use_piece=data["use_piece"] if data.get("use_piece") else False,
            grams_joint=data["grams_joint"],
            grams_piece=data["grams_piece"],
            order_number=order_number,
        )
        save(shop_to_price)
        invalidateShopCache(shop_to_price.shop_id)
        return shop_to_price, 201


@api.route("/<id>")
@api.doc("ShopToPrice detail operations.")
class ShopToPriceResource(Resource):
    @roles_accepted("admin")
    @marshal_with(shop_to_price_serializer_with_prices)
    def get(self, id):
        """List ShopToPrice"""
        item = load(ShopToPrice, id)
        price = Price.query.filter(Price.id == item.price_id).first()
        item.half = price.half if price.half else None
        item.one = price.one if price.one else None
        item.two_five = price.two_five if price.two_five else None
        item.five = price.five if price.five else None
        item.joint = price.joint if price.joint else None
        item.piece = price.piece if price.piece else None
        return item, 200

    @roles_accepted("admin")
    @api.expect(shop_to_price_serializer)
    @api.marshal_with(shop_to_price_serializer)
    def put(self, id):
        """Edit ShopToPrice"""
        item = load(ShopToPrice, id)

        # Todo increase validation -> if the update is correct
        price = Price.query.filter(Price.id == api.payload["price_id"]).first()
        shop = Shop.query.filter(Shop.id == api.payload["shop_id"]).first()
        kind = Kind.query.filter(Kind.id == api.payload["kind_id"]).first()
        product = Product.query.filter(Product.id == api.payload["product_id"]).first()

        if not price or not shop:
            abort(400, "Price or Shop not found")

        if (product and kind) or not product and not kind:
            abort(400, "One Cannabis or one Horeca product has to be provided")

        # Ok we survived all that: let's save it:
        item = update(item, api.payload)
        invalidateShopCache(item.shop_id)
        return item, 201

    @roles_accepted("admin")
    def delete(self, id):
        """Delete ShopToPrice"""
        item = load(ShopToPrice, id)
        invalidateShopCache(item.shop_id)
        delete(item)
        return "", 204


@api.route("/availability/<string:id>")
class ShopToPriceAvailability(Resource):
    @roles_accepted("admin")
    # @roles_accepted("employee")
    @api.expect(shop_to_price_availability_serializer)
    def put(self, id):
        shop_to_price = ShopToPrice.query.filter_by(id=id).first()
        shop_to_price.active = api.payload["active"]
        db.session.commit()
        invalidateShopCache(shop_to_price.shop_id)
        return 204
