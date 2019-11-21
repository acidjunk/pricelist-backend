import uuid

import structlog
from apis.helpers import get_range_from_args, get_sort_from_args, load, query_with_filters, save, update
from database import KindImage
from flask_restplus import Namespace, Resource, fields, marshal_with
from flask_security import roles_accepted
from werkzeug.datastructures import FileStorage

logger = structlog.get_logger(__name__)

api = Namespace("images", description="Image related operations")

image_serializer = api.model(
    "KindImage",
    {
        "id": fields.String(required=True),
        "original_name": fields.String(required=True, description="Original File Name"),
        "kind_id": fields.String(required=True, description="Kind Id"),
    },
)


parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")

upload_parser = api.parser()
upload_parser.add_argument("file", location="files", type=FileStorage, required=True)


@api.route("/")
@api.doc("Show all images.")
class KindImageResourceList(Resource):
    @roles_accepted("admin")
    @marshal_with(image_serializer)
    @api.doc(parser=parser)
    def get(self):
        """List Categories"""
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args)

        query_result, content_range = query_with_filters(KindImage, KindImage.query, range, sort, "")
        for result in query_result:
            result.shop_name = result.shop.name
            result.image_and_shop = f"{result.shop.name}:{result.name}"

        return query_result, 200, {"Content-Range": content_range}

    @roles_accepted("admin")
    # @api.expect(image_serializer)
    @api.expect(upload_parser)
    # @api.marshal_with(image_serializer)
    def post(self):
        """New Image"""
        image = KindImage(id=str(uuid.uuid4()), **api.payload)
        save(image)
        return image, 201


@api.route("/<id>")
@api.doc("Image detail operations.")
class KindImageResource(Resource):
    @roles_accepted("admin")
    @marshal_with(image_serializer)
    def get(self, id):
        """List Image"""
        item = load(KindImage, id)
        return item, 200

    @roles_accepted("admin")
    @api.expect(image_serializer)
    @api.marshal_with(image_serializer)
    def put(self, id):
        """Edit Image"""
        item = load(KindImage, id)
        item = update(item, api.payload)
        return item, 201
