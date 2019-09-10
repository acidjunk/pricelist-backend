import structlog
from apis.helpers import get_range_from_args, get_sort_from_args, query_with_filters
from database import User
from flask_restplus import Namespace, Resource, fields, marshal_with

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

    # @auth_token_required
    # @roles_accepted('admin', 'operator')
    @marshal_with(user_fields)
    @api.doc(parser=parser)
    def get(self):
        args = parser.parse_args()
        range = get_range_from_args(args)
        sort = get_sort_from_args(args, "username")

        query_result, content_range = query_with_filters(User, User.query, range, sort, "")
        return query_result, 200, {"Content-Range": content_range}


@api.route("/validate-email/<string:email>")
class ValidateEmailResource(Resource):
    def get(self, email):
        user = User.query.filter(User.email == email).first()
        if not user:
            return {"available": True, "reason": ""}
        else:
            return {"available": False, "reason": "Email already exists"}
