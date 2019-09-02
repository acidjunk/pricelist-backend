import structlog
from database import Category, Product, Shop
from flask_restplus import Namespace, Resource, fields, marshal_with

logger = structlog.get_logger(__name__)

api = Namespace("products", description="Product related operations")

price_fields = {"id": fields.String, "quantity": fields.Integer, "unit": fields.String, "price": fields.Float}

tag_fields = {"id": fields.String, "name": fields.String, "amount": fields.Integer}

product_marshaller = api.model(
    "Product",
    {
        "id": fields.String(required=True),
        "name": fields.String(required=True, description="Product name"),
        "description": fields.String(description="Description as shown in the product list"),
        "tags": fields.Nested(tag_fields),
        "shop": fields.String,
        "category": fields.String,
        "prices": fields.Nested(price_fields),
    },
)

shop_marshaller = api.model("Shop", {"id": fields.String, "name": fields.String})
category_marshaller = api.model("Category", {"id": fields.String, "name": fields.String})

product_list_fields = {
    "shop": fields.Nested(shop_marshaller),
    "category": fields.Nested(category_marshaller),
    "products": fields.List(fields.Nested(product_marshaller)),
}


@api.route("/shop/<shop_id>/category/<category_id>")
@api.doc("Show all products belonging to provided shop_id and category_id.")
class ProductResourceList(Resource):
    @marshal_with(product_list_fields)
    def get(self, shop_id, category_id):
        # Todo: return items from selected shop/category
        category = Category.query.filter_by(id=category_id).first()
        shop = Shop.query.filter_by(id=shop_id).first()
        products = Product.query.filter(Category.id == category_id).all()
        for product in products:
            product.tags = [
                {"id": tag.tag.id, "name": tag.tag.name, "amount": tag.amount} for tag in product.product_to_tags
            ]
            product.prices = [
                {"id": price.id, "quantity": price.quantity, "unit": price.unit, "price": price.price}
                for price in product.product_prices
            ]
        return {"shop": shop, "category": category, "products": products}
