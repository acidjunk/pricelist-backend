import structlog
from database import Shop
from flask_restplus import Namespace, Resource, fields, marshal_with

logger = structlog.get_logger(__name__)

api = Namespace("shops", description="Shop related operations")

shop_serializer = api.model(
    "Shop",
    {
        "id": fields.String(required=True),
        "name": fields.String(required=True, description="Unique Shop"),
        "description": fields.String(required=True, description="Shop description", default=False),
    },
)


@api.route("/")
@api.doc("Show all shops.")
class ShopResourceList(Resource):
    @marshal_with(shop_serializer)
    def get(self):
        return Shop.query.all()
