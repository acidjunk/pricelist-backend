from flask_restplus import Api

# from .v1.categories import api as categories_ns
# from .v1.products import api as products_ns
from .v1.shops import api as shops_ns
from .v1.users import api as users_ns

api = Api(title="Pricelist API", version="1.0", description="A restful api for the Pricelist")
api.add_namespace(shops_ns, path="/v1/shops")
# api.add_namespace(categories_ns, path="/v1/categories")
# api.add_namespace(products_ns, path="/v1/products")
api.add_namespace(users_ns, path="/v1/users")
