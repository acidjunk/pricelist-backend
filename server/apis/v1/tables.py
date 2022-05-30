import uuid

import structlog
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
from server.database import Table
from flask_restx import Namespace, Resource, fields, marshal_with
from flask_security import roles_accepted

logger = structlog.get_logger(__name__)

api = Namespace("tables", description="Table related operations")

table_serializer = api.model(
    "Table",
    {
        "id": fields.String(required=True),
        "name": fields.String(required=True, description="Table name"),
        "shop_id": fields.String(required=True, description="Shop Id"),
    },
)

table_serializer_with_shop_names = {
    "id": fields.String(required=True),
    "name": fields.String(required=True, description="Table name"),
    "shop_id": fields.String(required=True, description="Shop Id"),
    "shop_name": fields.String(description="Shop Name"),
}


parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")


@api.route("/")
@api.doc("Show all tables.")
class TableResourceList(Resource):
    @roles_accepted("admin")
    @marshal_with(table_serializer_with_shop_names)
    @api.doc(parser=parser)
    def get(self):
        """List Categories"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args)
        filter = get_filter_from_args(args)

        query_result, content_range = query_with_filters(Table, Table.query, range, sort, filter)
        for result in query_result:
            result.shop_name = result.shop.name
            result.table_and_shop = f"{result.shop.name}:{result.name}"

        return query_result, 200, {"Content-Range": content_range}

    @roles_accepted("admin")
    @api.expect(table_serializer)
    @api.marshal_with(table_serializer)
    def post(self):
        """New Table"""
        table = Table(id=str(uuid.uuid4()), **api.payload)
        save(table)
        return table, 201


@api.route("/<id>")
@api.doc("Table detail operations.")
class TableResource(Resource):
    @roles_accepted("admin")
    @marshal_with(table_serializer_with_shop_names)
    def get(self, id):
        """List Table"""
        item = load(Table, id)
        item.shop_name = item.shop.name
        item.table_and_shop = f"{item.shop.name}:{item.name}"
        return item, 200

    @roles_accepted("admin")
    @api.expect(table_serializer)
    @api.marshal_with(table_serializer)
    def put(self, id):
        """Edit Table"""
        item = load(Table, id)
        item = update(item, api.payload)
        return item, 201

    @roles_accepted("admin")
    def delete(self, id):
        """Delete Table"""
        item = load(Table, id)
        delete(item)
        return "", 204
