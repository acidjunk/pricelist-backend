import uuid

from apis.helpers import get_range_from_args, get_sort_from_args, load, query_with_filters, save, update
from database import Category, Kind, Price, Shop, ShopToPrice
from flask_restplus import Namespace, Resource, abort, fields, marshal_with
from flask_security import roles_accepted

api = Namespace("shops-to-prices", description="Shop to price related operations")

shop_to_price_serializer = api.model(
    "ShopToPrice",
    {
        "id": fields.String(),
        "active": fields.Boolean(default=True),
        "price_id": fields.String(required=True, description="Price Id"),
        "shop_id": fields.String(required=True, description="Shop Id"),
        "category_id": fields.String(description="Category Id"),
        "kind_id": fields.String(required=True, description="Kind Id"),
        "use_half": fields.Boolean(default=True, description="Use the price for 0.5g?"),
        "use_one": fields.Boolean(default=True, description="Use the price for 1?"),
        "use_two_five": fields.Boolean(default=True, description="Use the price for 2.5g?"),
        "use_five": fields.Boolean(default=True, description="Use the price for 5g?"),
        "use_joint": fields.Boolean(default=True, description="Use the price for joint?"),
        "use_piece": fields.Boolean(default=True, description="Use the price for piece?"),
    },
)

shop_to_price_serializer_with_prices = {
    "id": fields.String(),
    "active": fields.Boolean(default=True),
    "price_id": fields.String(required=True, description="Price Id"),
    "shop_id": fields.String(required=True, description="Shop Id"),
    "category_id": fields.String(description="Category Id"),
    "kind_id": fields.String(required=True, description="Kind Id"),
    "use_half": fields.Boolean(default=True, description="Show the price for 0.5g?"),
    "half": fields.String(description="Price for half gram"),
    "use_one": fields.Boolean(default=True, description="Show the price for 1?"),
    "one": fields.String(description="Price for one gram"),
    "use_two_five": fields.Boolean(default=True, description="Show the price for 2.5g?"),
    "two_five": fields.String(description="Price for two and a half gram"),
    "use_five": fields.Boolean(default=True, description="Show the price for 5g?"),
    "five": fields.String(description="Price for five gram"),
    "use_joint": fields.Boolean(default=True, description="Show the price for joint?"),
    "joint": fields.String(description="Price for one joint"),
    "use_piece": fields.Boolean(default=True, description="Show the price for one piece?"),
    "piece": fields.String(description="Price for one item"),
}

parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")


@api.route("/")
@api.doc("ShopsToPrices")
class ShopsToPricesResourceList(Resource):
    @marshal_with(shop_to_price_serializer)
    @api.doc(parser=parser)
    def get(self):
        """List prices for a shop"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args, "id")

        query_result, content_range = query_with_filters(
            ShopToPrice, ShopToPrice.query.filter_by(shop_id=id), range, sort, ""
        )
        return query_result, 200, {"Content-Range": content_range}

    @roles_accepted("admin")
    @api.expect(shop_to_price_serializer)
    @api.marshal_with(shop_to_price_serializer)
    def post(self):
        """Add new price rules to Shops"""
        price = Price.query.filter(Price.id == api.payload["price_id"]).first()
        shop = Shop.query.filter(Shop.id == api.payload["shop_id"]).first()
        kind = Kind.query.filter(Kind.id == api.payload["kind_id"]).first()
        category = None
        if api.payload.get("category_id"):
            category = Category.query.filter(Category.id == api.payload["category_id"]).first()

        if not price or not shop or not kind:
            abort(400, "Price or shop or kind not found")

        check_query = (
            ShopToPrice.query.filter_by(shop_id=shop.id).filter_by(price_id=price.id).filter_by(kind_id=kind.id).all()
        )
        if len(check_query) > 0:
            abort(409, "Relation already exists")

        data = api.payload
        shop_to_price = ShopToPrice(
            id=str(uuid.uuid4()),
            active=data["active"] if data.get("active") else False,
            kind=kind,
            category=category,
            shop=shop,
            price=price,
            use_half=data["use_half"] if data.get("use_half") else False,
            use_one=data["use_one"] if data.get("use_one") else False,
            use_two_five=data["use_two_five"] if data.get("use_two_five") else False,
            use_five=data["use_five"] if data.get("use_five") else False,
            use_joint=data["use_joint"] if data.get("use_joint") else False,
            use_piece=data["use_piece"] if data.get("use_piece") else False,
        )
        save(shop_to_price)
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
        item.half = price.half if price.half else "N/A"
        item.one = price.one if price.one else "N/A"
        item.two_five = price.two_five if price.two_five else "N/A"
        item.five = price.five if price.five else "N/A"
        item.joint = price.joint if price.joint else "N/A"
        item.piece = price.piece if price.piece else "N/A"

        return item, 200

    @roles_accepted("admin")
    @api.expect(shop_to_price_serializer)
    @api.marshal_with(shop_to_price_serializer)
    def put(self, id):
        """Edit ShopToPrice"""
        item = load(ShopToPrice, id)
        item = update(item, api.payload)
        return item, 201
