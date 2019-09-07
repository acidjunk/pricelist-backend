import copy
import hashlib
import uuid
from datetime import datetime

import structlog
from apis.helpers import _user_query_with_filters
from database import User, db
from flask_login import current_user
from flask_restplus import Namespace, Resource, abort, fields, marshal_with
from flask_security import auth_token_required, roles_accepted

logger = structlog.get_logger(__name__)

api = Namespace("users", description="User related operations")

user_fields = {
    "id": fields.String,
    "username": fields.String,
    "email": fields.String,
    "first_name": fields.String,
    "last_name": fields.String,
    "created_at": fields.DateTime,
    "confirmed_at": fields.DateTime,
    "roles": fields.List(fields.String),
    "mail_offers": fields.Boolean,
}

user_message_fields = {"available": fields.Boolean, "reason": fields.String}

parser = api.parser()
parser.add_argument("range", location="args", help="Pagination")
parser.add_argument("filter", location="args", help="Filter list options")
parser.add_argument("sort", location="args", help="Sort list options")


@api.route("/")
@api.doc("Show all users to staff users.")
class UserResourceList(Resource):

    # @auth_token_required
    # @roles_accepted('admin', 'operator')
    @marshal_with(user_fields)
    def get(self):
        args = parser.parse_args()
        range = []
        if args["range"]:
            try:
                input = args["range"][1:-1].split(",")
                for i in input:
                    range.append(int(i))
            except:
                range = [0, 19]
            logger.info("Query parameters", range=range)

        sort = []
        if args["sort"]:
            try:
                input = args["sort"].split(",")
                sort.append(input[0][2:-1])
                sort.append(input[1][1:-2])
            except:
                sort = []
            logger.info("Query parameters", sort=sort)
        query_result, content_range = _user_query_with_filters(User.query, range, sort, "")
        return query_result, 200, {"Content-Range": content_range}


@api.route("/validate-email/<string:email>")
class ValidateEmailResource(Resource):
    def get(self, email):
        user = User.query.filter(User.email == email).first()
        if not user:
            return {"available": True, "reason": ""}
        else:
            return {"available": False, "reason": "Email already exists"}
