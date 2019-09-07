from flask_restplus import Api

from .v1.flavors import api as flavors_ns
from .v1.kinds import api as kinds_ns
from .v1.shops import api as shops_ns
from .v1.tags import api as tags_ns
from .v1.users import api as users_ns

api = Api(title="Pricelist API", version="1.0", description="A restful api for the Pricelist")
api.add_namespace(shops_ns, path="/v1/shops")
api.add_namespace(flavors_ns, path="/v1/flavors")
api.add_namespace(tags_ns, path="/v1/tags")
api.add_namespace(kinds_ns, path="/v1/kinds")
api.add_namespace(users_ns, path="/v1/users")
