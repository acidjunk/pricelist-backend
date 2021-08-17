import structlog
from apis.helpers import get_filter_from_args, get_range_from_args, get_sort_from_args, query_with_filters
from database import User
from flask_login import current_user
from flask_restx import Namespace, Resource, abort, fields, marshal_with
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
parser.add_argument("range", location="args", help="Pagination: default=[0,19]")
parser.add_argument("sort", location="args", help='Sort: default=["name","ASC"]')
parser.add_argument("filter", location="args", help="Filter default=[]")


@api.route("/")
@api.doc("Show all users to staff users.")
class UserResourceList(Resource):
    # @roles_accepted("admin")
    @marshal_with(user_fields)
    @api.doc(parser=parser)
    def get(self):
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args, "username")
        filter = get_filter_from_args(args)

        query_result, content_range = query_with_filters(
            User, User.query, range, sort, filter, quick_search_columns=["username", "email"]
        )
        return query_result, 200, {"Content-Range": content_range}


@api.route("/validate-email/<string:email>")
class ValidateEmailResource(Resource):
    def get(self, email):
        user = User.query.filter(User.email == email).first()
        if not user:
            return {"available": True, "reason": ""}
        else:
            return {"available": False, "reason": "Email already exists"}


@api.route("/current-user")
@api.doc("Retrieve info about currently logged in user.")
class UserResource(Resource):
    @auth_token_required
    @marshal_with({**user_fields})
    def get(self):
        user = User.query.filter(User.id == current_user.id).first()
        if not user:
            abort(400, "Unknown user")
        return user


@api.route("/me")
@api.doc("Retrieve info about currently logged in user.")
class UserResourceCookie(Resource):
    @roles_accepted("admin", "moderator", "operator", "employee", "staff")
    @marshal_with({**user_fields})
    def get(self):
        user = User.query.filter(User.id == current_user.id).first()
        if not user:
            abort(400, "Unknown user")
        return user
