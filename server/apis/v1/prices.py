import structlog
from database import db
from flask_restplus import Namespace, Resource, fields, marshal_with
from database import Category, Item, Shop

logger = structlog.get_logger(__name__)

api = Namespace("prices", description="Pricelist related operations")

item_serializer = api.model("Item", {
    "name": fields.String(required=True, description="Item name"),
})

category_serializer = api.model("Category", {
    "name": fields.String(required=True, description="Category name"),
    "description": fields.String(description="Description as shown in the category list and overviews")
})

shop_serializer = api.model("Shop", {
    "id": fields.String(required=True),
    "name": fields.String(required=True, description="Unique exercise name"),
    "description": fields.String(required=True, description="Description", default=False),
})


@api.route('/')
class ShopResourceList(Resource):

    @marshal_with(shop_serializer)
    def get(self):
        # Get public exercises and exercises owned by this user
        return Shop.query.all()

@api.route('/')
class CategoryResourceList(Resource):

    @marshal_with(category_serializer)
    def get(self):
        # Todo: return categories from selected shop
        return Category.query.all()


@api.route('/category')
@api.doc("Show all riffs to users with sufficient rights. Provides the ability to filter on riff status and to search.")
class ItemResourceList(Resource):

    @marshal_with(item_serializer)
    def get(self):
        # Todo: return items from selected shop/category
        return Item.query.all()
