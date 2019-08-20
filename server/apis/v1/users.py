import copy

from datetime import datetime
import hashlib
import uuid

import structlog
from flask_login import current_user

from flask_restplus import Namespace, Resource, fields, marshal_with, abort
from database import User, db
from flask_security import auth_token_required, roles_accepted

logger = structlog.get_logger(__name__)

api = Namespace("users", description="User related operations")

user_fields = {
    'id': fields.String,
    'username': fields.String,
    'email': fields.String,
    'first_name': fields.String,
    'last_name': fields.String,
    'created_at': fields.DateTime,
    'confirmed_at': fields.DateTime,
    'roles': fields.List(fields.String),
    'mail_offers': fields.Boolean,
}

user_message_fields = {
   'available': fields.Boolean,
   'reason': fields.String,
}


@api.route('/')
@api.doc("Show all users to staff users.")
class UserResourceList(Resource):

    @auth_token_required
    @roles_accepted('admin', 'operator')
    @marshal_with(user_fields)
    def get(self):
        users = User.query.all()
        return users


@api.route('/validate-email/<string:email>')
class ValidateEmailResource(Resource):

    def get(self, email):
        user = User.query.filter(User.email == email).first()
        if not user:
            return {'available': True, 'reason': ''}
        else:
            return {'available': False, 'reason': 'Email already exists'}
