import uuid

import structlog
from apis.helpers import (
    delete,
    get_filter_from_args,
    get_range_from_args,
    get_sort_from_args,
    load,
    query_with_filters,
    save,
    update,
)
from database import Strain
from flask_restx import Namespace, Resource, fields, marshal_with
from flask_security import roles_accepted

logger = structlog.get_logger(__name__)

api = Namespace("strains", description="Strain related operations")

strain_serializer = api.model(
    "Strain",
    {
        "id": fields.String(),
        "name_nl": fields.String(required=True, description="Unique EN strain name"),
        "name_en": fields.String(required=True, description="Unique EN strain name"),
    },
)

parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")


@api.route("/")
@api.doc("Show all strains.")
class StrainResourceList(Resource):
    @roles_accepted("admin")
    @marshal_with(strain_serializer)
    @api.doc(parser=parser)
    def get(self):
        """List Strains"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args, "name_nl")
        filter = get_filter_from_args(args)

        query_result, content_range = query_with_filters(Strain, Strain.query, range, sort, filter)
        return query_result, 200, {"Content-Range": content_range}

    @roles_accepted("admin")
    @api.expect(strain_serializer)
    @api.marshal_with(strain_serializer)
    def post(self):
        """New Strains"""
        strain = Strain(id=str(uuid.uuid4()), **api.payload)
        save(strain)
        return strain, 201


@api.route("/<id>")
@api.doc("Strain detail operations.")
class StrainResource(Resource):
    @roles_accepted("admin")
    @marshal_with(strain_serializer)
    def get(self, id):
        """List Strain"""
        item = load(Strain, id)
        return item, 200

    @roles_accepted("admin")
    @api.expect(strain_serializer)
    @api.marshal_with(strain_serializer)
    def put(self, id):
        """Edit Strain"""
        item = load(Strain, id)
        item = update(item, api.payload)
        return item, 201

    @roles_accepted("admin")
    def delete(self, id):
        """Edit Strain"""
        item = load(Strain, id)
        delete(item)
        return "", 204
