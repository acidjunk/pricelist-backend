import uuid

from server.apis.helpers import (
    delete,
    get_filter_from_args,
    get_range_from_args,
    get_sort_from_args,
    load,
    query_with_filters,
    save,
    update,
)
from server.database import Kind, KindToStrain, Strain
from flask_restx import Namespace, Resource, abort, fields, marshal_with
from flask_security import roles_accepted

api = Namespace("kinds-to-strains", description="Kind to strain related operations")

kind_to_strain_serializer = api.model(
    "KindToStrain",
    {
        "id": fields.String(),
        "strain_id": fields.String(required=True, description="Strain Id"),
        "kind_id": fields.String(required=True, description="Kind Id"),
    },
)

parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")


@api.route("/")
@api.doc("KindToStrain relations")
class KindsToStrainsResourceList(Resource):
    @marshal_with(kind_to_strain_serializer)
    @api.doc(parser=parser)
    def get(self):
        """List strains for a product kind"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args, "id")
        filter = get_filter_from_args(args)

        query_result, content_range = query_with_filters(KindToStrain, KindToStrain.query, range, sort, filter)
        return query_result, 200, {"Content-Range": content_range}

    @roles_accepted("admin")
    @api.expect(kind_to_strain_serializer)
    @api.marshal_with(kind_to_strain_serializer)
    def post(self):
        """New KindToStrain"""
        strain = Strain.query.filter(Strain.id == api.payload["strain_id"]).first()
        kind = Kind.query.filter(Kind.id == api.payload["kind_id"]).first()

        if not strain or not kind:
            abort(400, "Strain or kind not found")

        check_query = KindToStrain.query.filter_by(kind_id=kind.id).filter_by(strain_id=strain.id).all()
        if len(check_query) > 0:
            abort(409, "Relation already exists")

        kind_to_strain = KindToStrain(id=str(uuid.uuid4()), kind=kind, strain=strain)
        save(kind_to_strain)

        kind.complete = (
            True
            if len(kind.kind_strains) + 1 >= 3
            and len(kind.kind_tags) >= 4
            and kind.image_1
            and kind.description_nl
            and kind.description_en
            else False
        )
        save(kind)

        return kind_to_strain, 201


@api.route("/<id>")
@api.doc("KindToStrain detail operations.")
class KindsToStrainsResource(Resource):
    @roles_accepted("admin")
    @marshal_with(kind_to_strain_serializer)
    def get(self, id):
        """List KindToStrain"""
        item = load(KindToStrain, id)
        return item, 200

    @roles_accepted("admin")
    @api.expect(kind_to_strain_serializer)
    @api.marshal_with(kind_to_strain_serializer)
    def put(self, id):
        """Edit KindToStrain"""
        item = load(KindToStrain, id)
        item = update(item, api.payload)
        return item, 201

    @roles_accepted("admin")
    def delete(self, id):
        """Edit Tag"""
        item = load(KindToStrain, id)
        delete(item)
        return "", 204
