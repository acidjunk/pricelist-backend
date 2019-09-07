import structlog
from database import Kind
from flask_restplus import Namespace, Resource, fields, marshal_with

logger = structlog.get_logger(__name__)

api = Namespace("kinds", description="Kind related operations")

tag_fields = {"id": fields.String, "name": fields.String, "amount": fields.Integer}
flavor_fields = {"id": fields.String, "name": fields.String, "icon": fields.String, "color": fields.String}

kind_marshaller = api.model(
    "Kind",
    {
        "id": fields.String(required=True),
        "name": fields.String(required=True, description="Product name"),
        "short_description_nl": fields.String(description="NL Description as shown in the price list"),
        "description_nl": fields.String(description="EN Description as shown in the detail view"),
        "short_description_en": fields.String(description="NL Description as shown in the price list"),
        "description_en": fields.String(description="EN Description as shown in the detail view"),
        "tags": fields.Nested(tag_fields),
        "flavors": fields.Nested(flavor_fields),
    },
)


@api.route("/")
@api.doc("Show all kinds.")
class KindResourceList(Resource):
    @marshal_with(kind_marshaller)
    def get(self):
        # Todo: return items from selected shop/category
        kinds = Kind.query.all()
        for kind in kinds:
            kind.tags = [{"id": tag.tag.id, "name": tag.tag.name, "amount": tag.amount} for tag in kind.kind_to_tags]
            kind.flavors = [
                {
                    "id": flavor.flavor.id,
                    "name": flavor.flavor.name,
                    "icon": flavor.flavor.icon,
                    "color": flavor.flavor.color,
                }
                for flavor in kind.kind_to_flavors
            ]
        return kinds
