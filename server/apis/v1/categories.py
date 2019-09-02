import structlog
from database import Category, Shop
from flask_restplus import Namespace, Resource, fields, marshal_with

logger = structlog.get_logger(__name__)

api = Namespace("categories", description="Shop category related operations")

category_marshaller = api.model(
    "Category",
    {
        "id": fields.String(required=True),
        "name": fields.String(required=True, description="Category name"),
        "description": fields.String(description="Description as shown in the category list and overviews"),
        "shop": fields.String(required=True, description="Shop name"),
    },
)
shop_marshaller = api.model("Shop", {"id": fields.String, "name": fields.String})

category_list_fields = {
    "shop": fields.Nested(shop_marshaller),
    "categories": fields.List(fields.Nested(category_marshaller)),
}


@api.route("/shop/<shop_id>")
@api.doc("Show all categories belonging to provided shop_id.")
class CategoryResourceList(Resource):
    @marshal_with(category_list_fields)
    def get(self, shop_id):
        # Todo: return categories from selected shop
        shop = Shop.query.filter_by(id=shop_id).first()
        return {"shop": shop, "categories": Category.query.filter_by(shop_id=shop_id).all()}
