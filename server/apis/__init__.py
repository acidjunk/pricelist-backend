from flask_restplus import Api

from .v1.prices import api as prices_ns
from .v1.users import api as users_ns

api = Api(
    title='Pricelist API',
    version='1.0',
    description='A restful api for the Pricelist',
)
api.add_namespace(prices_ns, path='/v1/prices')
api.add_namespace(users_ns, path='/v1/users')
