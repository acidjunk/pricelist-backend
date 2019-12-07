import uuid

from apis.helpers import get_range_from_args, get_sort_from_args, load, query_with_filters, save, update
from database import Kind, KindToTag, Tag
from flask_restplus import Namespace, Resource, abort, fields, marshal_with
from flask_security import roles_accepted

api = Namespace("kinds-to-tags", description="Kind to tag related operations")

kind_to_tag_serializer = api.model(
    "KindToTag",
    {
        "id": fields.String(),
        "amount": fields.Integer(required=True, description="Effect amount"),
        "tag_id": fields.String(required=True, description="Tag Id"),
        "kind_id": fields.String(required=True, description="Kind Id"),
    },
)

parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")


@api.route("/")
@api.doc("Create tags")
class KindsToTagsResourceList(Resource):
    @marshal_with(kind_to_tag_serializer)
    @api.doc(parser=parser)
    def get(self):
        """List tags for a product kind"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args, "amount")

        query_result, content_range = query_with_filters(KindToTag, KindToTag.query, range, sort, "")
        return query_result, 200, {"Content-Range": content_range}

    @roles_accepted("admin")
    @api.expect(kind_to_tag_serializer)
    @api.marshal_with(kind_to_tag_serializer)
    def post(self):
        """New KindToTag"""
        tag = Tag.query.filter(Tag.id == api.payload["tag_id"]).first()
        kind = Kind.query.filter(Kind.id == api.payload["kind_id"]).first()

        if not tag or not kind:
            abort(400, "Tag or kind not found")

        check_query = KindToTag.query.filter_by(kind_id=kind.id).filter_by(tag_id=tag.id).all()
        if len(check_query) > 0:
            abort(409, "Relation already exists")

        kind_to_tag = KindToTag(id=str(uuid.uuid4()), kind=kind, tag=tag, amount=api.payload["amount"])
        save(kind_to_tag)

        kind.complete = (
            True
            if len(kind.kind_flavors) >= 3
            and len(kind.kind_tags) + 1 >= 4
            and kind.image_1
            and kind.description_nl
            and kind.description_en
            else False
        )
        save(kind)

        return kind_to_tag, 201


@api.route("/<id>")
@api.doc("KindToTag detail operations.")
class KindsToTagsResource(Resource):
    @roles_accepted("admin")
    @marshal_with(kind_to_tag_serializer)
    def get(self, id):
        """List KindToTag"""
        item = load(KindToTag, id)
        return item, 200

    @roles_accepted("admin")
    @api.expect(kind_to_tag_serializer)
    @api.marshal_with(kind_to_tag_serializer)
    def put(self, id):
        """Edit KindToTag"""
        item = load(KindToTag, id)
        item = update(item, api.payload)
        return item, 201
