import os

import structlog
from apis.helpers import get_range_from_args, get_sort_from_args, load, query_with_filters, update
from database import KindImage
from flask import current_app
from flask_restplus import Namespace, Resource, abort, fields, marshal_with, reqparse
from flask_security import roles_accepted
from werkzeug.datastructures import FileStorage

logger = structlog.get_logger(__name__)

api = Namespace("images", description="Image related operations")

image_serializer = api.model(
    "KindImage",
    {
        "id": fields.String(required=True),
        "name": fields.String(required=True, description="File Name"),
        "kind_id": fields.String(required=True, description="Kind Id"),
    },
)


parser = api.parser()
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")

file_upload = reqparse.RequestParser()
file_upload.add_argument("file", type=FileStorage, location="files", required=True, help="file")


@api.route("/upload/")
class FileUpload(Resource):
    @api.expect(file_upload)
    def post(self):
        args = file_upload.parse_args()
        if args["file"].mimetype == "application/png" or 1:
            destination = os.path.join(current_app.config.get("DATA_FOLDER"), "medias/")
            if not os.path.exists(destination):
                os.makedirs(destination)
            png_file = "%s%s" % (destination, "custom_file_name.png")
            args["file"].save(png_file)
        else:
            abort(404)
        return {"status": "Done"}


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
