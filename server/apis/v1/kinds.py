import uuid

import structlog
from apis.helpers import get_range_from_args, get_sort_from_args, load, query_with_filters, save, update
from database import Flavor, Kind, KindToFlavor, KindToTag, Tag
from flask_restplus import Namespace, Resource, abort, fields, marshal_with

logger = structlog.get_logger(__name__)

api = Namespace("kinds", description="Kind related operations")

tag_fields = {"id": fields.String, "name": fields.String, "amount": fields.Integer}
flavor_fields = {"id": fields.String, "name": fields.String, "icon": fields.String, "color": fields.String}

kind_serializer = api.model(
    "Kind",
    {
        "id": fields.String(),
        "name": fields.String(required=True, description="Product name"),
        "short_description_nl": fields.String(description="NL Description as shown in the price list"),
        "description_nl": fields.String(description="EN Description as shown in the detail view"),
        "short_description_en": fields.String(description="NL Description as shown in the price list"),
        "description_en": fields.String(description="EN Description as shown in the detail view"),
    },
)

kind_serializer_with_relations = {
    "id": fields.String(),
    "name": fields.String(required=True, description="Product name"),
    "short_description_nl": fields.String(description="NL Description as shown in the price list"),
    "description_nl": fields.String(description="EN Description as shown in the detail view"),
    "short_description_en": fields.String(description="NL Description as shown in the price list"),
    "description_en": fields.String(description="EN Description as shown in the detail view"),
    "tags": fields.Nested(tag_fields),
    "flavors": fields.Nested(flavor_fields),
}

kind_to_tag_serializer = api.model(
    "KindToTag",
    {
        "id": fields.String(),
        "amount": fields.Integer(required=True, description="Effect amount"),
        "tag_id": fields.String(required=True, description="Tag Id"),
        "kind_id": fields.String(required=True, description="Kind Id"),
    },
)

kind_to_flavor_serializer = api.model(
    "KindToFlavor",
    {
        "id": fields.String(),
        "flavor_id": fields.String(required=True, description="Flavor Id"),
        "kind_id": fields.String(required=True, description="Kind Id"),
    },
)


parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")


@api.route("/")
@api.doc("Show all kinds.")
class KindResourceList(Resource):
    @marshal_with(kind_serializer_with_relations)
    @api.doc(parser=parser)
    def get(self):
        """List (Product)Kinds"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args)

        query_result, content_range = query_with_filters(Kind, Kind.query, range, sort, "")
        # Todo: return items from selected shop/category
        for kind in query_result:
            kind.tags = [
                {"id": tag.tag.id, "name": f"{tag.tag.name}: {tag.amount}", "amount": tag.amount}
                for tag in kind.kind_to_tags
            ]
            kind.flavors = [
                {
                    "id": flavor.flavor.id,
                    "name": flavor.flavor.name,
                    "icon": flavor.flavor.icon,
                    "color": flavor.flavor.color,
                }
                for flavor in kind.kind_to_flavors
            ]
        return query_result, 200, {"Content-Range": content_range}

    @api.expect(kind_serializer)
    @api.marshal_with(kind_serializer)
    def post(self):
        """New Shops"""
        kind = Kind(id=str(uuid.uuid4()), **api.payload)
        save(kind)
        return kind, 201


@api.route("/<id>")
@api.doc("Kind detail operations.")
class KindResource(Resource):
    @marshal_with(kind_serializer)
    def get(self, id):
        """List Kind"""
        item = load(Kind, id)
        return item, 200

    @api.expect(kind_serializer)
    @api.marshal_with(kind_serializer)
    def put(self, id):
        """Edit Kind"""
        item = load(Kind, id)
        item = update(item, api.payload)
        return item, 201


@api.route("/<id>/tags")
@api.doc("Show all tags for a kind")
class KindDetailTagResourceList(Resource):
    @marshal_with(kind_to_tag_serializer)
    @api.doc(parser=parser)
    def get(self, id):
        """List tags for a product kind"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args, "amount")

        query_result, content_range = query_with_filters(
            KindToTag, KindToTag.query.filter_by(kind_id=id), range, sort, ""
        )
        return query_result, 200, {"Content-Range": content_range}


@api.route("/tags")
@api.doc("Create tags")
class NewKindToTagResource(Resource):
    @api.expect(kind_to_tag_serializer)
    @api.marshal_with(kind_to_tag_serializer)
    def post(self):
        """New Shops"""
        tag = Tag.query.filter(Tag.id == api.payload["tag_id"]).first()
        kind = Kind.query.filter(Kind.id == api.payload["kind_id"]).first()

        if not tag or not kind:
            abort(400, "Tag or kind not found")

        check_query = KindToTag.query.filter_by(kind_id=kind.id).filter_by(tag_id=tag.id).all()
        if len(check_query) > 0:
            abort(409, "Relation already exists")

        kind_to_tag = KindToTag(id=str(uuid.uuid4()), kind=kind, tag=tag, amount=api.payload["amount"])
        save(kind_to_tag)
        return kind_to_tag, 201


@api.route("/tag/<id>")
@api.doc("KindToTag detail operations.")
class KindToTagResource(Resource):
    @marshal_with(kind_to_tag_serializer)
    def get(self, id):
        """List KindToTag"""
        item = load(KindToTag, id)
        return item, 200

    @api.expect(kind_to_tag_serializer)
    @api.marshal_with(kind_to_tag_serializer)
    def put(self, id):
        """Edit KindToTag"""
        item = load(KindToTag, id)
        item = update(item, api.payload)
        return item, 201


@api.route("/<id>/flavors")
@api.doc("Show all flavors for a kind")
class KindDetailFlavorResourceList(Resource):
    @marshal_with(kind_to_flavor_serializer)
    @api.doc(parser=parser)
    def get(self, id):
        """List flavors for a product kind"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args, "id")

        query_result, content_range = query_with_filters(
            KindToFlavor, KindToFlavor.query.filter_by(kind_id=id), range, sort, ""
        )
        return query_result, 200, {"Content-Range": content_range}


@api.route("/flavors")
@api.doc("Create flavors")
class NewKindToFlavorResource(Resource):
    @api.expect(kind_to_flavor_serializer)
    @api.marshal_with(kind_to_flavor_serializer)
    def post(self):
        """New Shops"""
        flavor = Flavor.query.filter(Flavor.id == api.payload["flavor_id"]).first()
        kind = Kind.query.filter(Kind.id == api.payload["kind_id"]).first()

        if not flavor or not kind:
            abort(400, "Flavor or kind not found")

        check_query = KindToFlavor.query.filter_by(kind_id=kind.id).filter_by(flavor_id=flavor.id).all()
        if len(check_query) > 0:
            abort(409, "Relation already exists")

        kind_to_flavor = KindToFlavor(id=str(uuid.uuid4()), kind=kind, flavor=flavor)
        save(kind_to_flavor)
        return kind_to_flavor, 201


@api.route("/tag/<id>")
@api.doc("KindToFlavor detail operations.")
class KindToFlavorResource(Resource):
    @marshal_with(kind_to_flavor_serializer)
    def get(self, id):
        """List KindToFlavor"""
        item = load(KindToFlavor, id)
        return item, 200

    @api.expect(kind_to_flavor_serializer)
    @api.marshal_with(kind_to_flavor_serializer)
    def put(self, id):
        """Edit KindToFlavor"""
        item = load(KindToFlavor, id)
        item = update(item, api.payload)
        return item, 201
