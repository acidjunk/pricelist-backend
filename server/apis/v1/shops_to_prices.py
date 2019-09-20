import uuid

from apis.helpers import get_range_from_args, get_sort_from_args, load, query_with_filters, save, update
from database import Price, Shop, ShopToPrice
from flask_restplus import Namespace, Resource, abort, fields, marshal_with
from flask_security import roles_accepted

api = Namespace("shops-to-prices", description="Shop to price related operations")

shop_to_price_serializer = api.model(
    "ShopToPrice",
    {
        "id": fields.String(),
        "price_id": fields.String(required=True, description="Price Id"),
        "shop_id": fields.String(required=True, description="Shop Id"),
        "category_id": fields.String(description="Category Id"),
        "kind_id": fields.String(required=True, description="Kind Id"),
        "use_half": fields.Boolean(description="Use the price for 0.5g?"),
        "use_one": fields.Boolean(description="Use the price for 1?"),
        "use_two_five": fields.Boolean(description="Use the price for 2.5g?"),
        "use_five": fields.Boolean(description="Use the price for 5g?"),
        "use_joint": fields.Boolean(description="Use the price for joint?"),
        "use_piece": fields.Boolean(description="Use the price for piece?"),
    },
)

parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")


@api.route("/")
@api.doc("ShopsToFlavos")
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

        # Todo: category...

        if not price or not shop:
            abort(400, "Price or shop not found")

        check_query = ShopToPrice.query.filter_by(shop_id=shop.id).filter_by(price_id=price.id).all()
        if len(check_query) > 0:
            abort(409, "Relation already exists")

        data = api.payload
        shop_to_price = ShopToPrice(
            id=str(uuid.uuid4()),
            active=data["active"],
            shop=shop,
            price=price,
            half=data["half"],
            one=data["one"],
            two_five=data["two_five"],
            five=data["five"],
            joint=data["joint"],
            piece=data["piece"],
        )
        save(shop_to_price)
        return shop_to_price, 201


@api.route("/<id>")
@api.doc("ShopToPrice detail operations.")
class ShopToPriceResource(Resource):
    @roles_accepted("admin")
    @marshal_with(shop_to_price_serializer)
    def get(self, id):
        """List ShopToPrice"""
        item = load(ShopToPrice, id)
        return item, 200

    @roles_accepted("admin")
    @api.expect(shop_to_price_serializer)
    @api.marshal_with(shop_to_price_serializer)
    def put(self, id):
        """Edit ShopToPrice"""
        item = load(ShopToPrice, id)
        item = update(item, api.payload)
        return item, 201
