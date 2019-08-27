import structlog
from database import Category
from flask_restplus import Namespace, Resource, fields, marshal_with

logger = structlog.get_logger(__name__)

api = Namespace("categories", description="Shop category related operations")

category_serializer = api.model(
    "Category",
    {
        "id": fields.String(required=True),
        "name": fields.String(required=True, description="Category name"),
        "description": fields.String(description="Description as shown in the category list and overviews"),
        "shop": fields.String(required=True, description="Shop name"),
    },
)


@api.route("/shop/<shop_id>")
@api.doc("Show all categories belonging to provided shop_id.")
class CategoryResourceList(Resource):
    @marshal_with(category_serializer)
    def get(self, shop_id):
        # Todo: return categories from selected shop
        return Category.query.filter_by(shop_id=shop_id).all()
