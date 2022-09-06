import io
import os
import traceback
from functools import wraps
from http import HTTPStatus
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, cast

import click
import flask
import structlog
from admin_views import (
    BaseAdminView,
    CategoryAdminView,
    KindAdminView,
    OrderAdminView,
    PriceAdminView,
    RolesAdminView,
    ShopAdminView,
    UserAdminView,
)
from apis import api
from database import (
    Category,
    Flavor,
    Kind,
    KindToFlavor,
    KindToTag,
    MainCategory,
    Order,
    Price,
    Role,
    Shop,
    ShopToPrice,
    Tag,
    User,
    db,
    user_datastore,
)
from flask import Flask, jsonify, request, url_for
from flask_admin import Admin
from flask_admin import helpers as admin_helpers
from flask_cors import CORS
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_security import Security, user_registered
from form import create_product_form, create_strain_form
from pydantic_forms.core import register_form, start_form, list_forms
from pydantic_forms.exceptions import FormNotCompleteError, FormValidationError
from pydantic_forms.types import JSON
from security import ExtendedJSONRegisterForm, ExtendedRegisterForm
from utils import generate_qr_image, import_prices
from version import VERSION

logger = structlog.get_logger(__name__)

# Create app
app = Flask(__name__, static_url_path="/static")
app.url_map.strict_slashes = False
# NOTE: the extra headers need to be available in the API gateway: that is handled by zappa_settings.json
CORS(
    app,
    supports_credentials=True,
    resources="/*",
    allow_headers="*",
    origins="*",
    expose_headers="Authorization,Content-Type,Authentication-Token,Content-Range",
)
DATABASE_URI = os.getenv("DATABASE_URI", "postgres://postgres:@localhost/pricelist-test")  # setup Travis

app.config["DEBUG"] = False if not os.getenv("DEBUG") else True
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY") if os.getenv("SECRET_KEY") else "super-secret"
admin = Admin(app, name="Pricelist", template_mode="bootstrap3")

app.config["VERSION"] = VERSION
app.config["FLASK_ADMIN_SWATCH"] = "flatly"
app.config["FLASK_ADMIN_FLUID_LAYOUT"] = True
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY") if os.getenv("SECRET_KEY") else "super-secret"
app.config["SECURITY_PASSWORD_HASH"] = "pbkdf2_sha256"
app.config["SECURITY_PASSWORD_SALT"] = (
    os.getenv("SECURITY_PASSWORD_SALT") if os.getenv("SECURITY_PASSWORD_SALT") else "SALTSALTSALT"
)
# More Flask Security settings
app.config["SECURITY_REGISTERABLE"] = True
app.config["SECURITY_CONFIRMABLE"] = True
app.config["SECURITY_RECOVERABLE"] = True
app.config["SECURITY_CHANGEABLE"] = True
app.config["SECURITY_USER_IDENTITY_ATTRIBUTES"] = ["email"]
app.config["SECURITY_BACKWARDS_COMPAT_AUTH_TOKEN"] = True

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
app.config["SQLALCHEMY_COMMIT_ON_TEARDOWN"] = True
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Replace the next six lines with your own SMTP server settings
app.config["SECURITY_EMAIL_SENDER"] = (
    os.getenv("SECURITY_EMAIL_SENDER") if os.getenv("SECURITY_EMAIL_SENDER") else "no-reply@example.com"
)
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER") if os.getenv("MAIL_SERVER") else "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME") if os.getenv("MAIL_USERNAME") else "no-reply@example.com"
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD") if os.getenv("MAIL_PASSWORD") else "somepassword"

# Needed for Forms to not mess up form order
app.config['JSON_SORT_KEYS'] = False

app.config["FRONTEND_URI"] = os.getenv("FRONTEND_URI") if os.getenv("FRONTEND_URI") else "www.example.com"
# Todo: check if we can fix this without completely disabling it: it's only needed when login request is not via .json
app.config["WTF_CSRF_ENABLED"] = False

# The S3 Bucket for file storage. Note: IMAGE_S3_ACCESS_KEY_ID and IMAGE_S3_SECRET_ACCESS_KEY are also needed!
app.config["IMAGE_BUCKET"] = os.getenv("IMAGE_S3_BUCKET") if os.getenv("IMAGE_S3_BUCKET") else "image-prijslijst.info"

# Setup Flask-Security with extended user registration
security = Security(
    app, user_datastore, register_form=ExtendedRegisterForm, confirm_register_form=ExtendedJSONRegisterForm
)
login_manager = LoginManager(app)
mail = Mail()
register_form("create_product_form", create_product_form)
register_form("create_strain_form", create_strain_form)


@app.cli.command("import-prices")
@click.argument("file")
def import_prices_click(file):
    import_prices(file)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()


# define a context processor for merging flask-admin's template context into the
# flask-security views.
@security.context_processor
def security_context_processor():
    return dict(admin_base_template=admin.base_template, admin_view=admin.index_view, h=admin_helpers, get_url=url_for)


# ensure that new users are in an role
@user_registered.connect_via(app)
def on_user_registered(sender, user, confirm_token):
    user_datastore.add_role_to_user(user, "customer")
    # Todo: Not sure if we need this commit
    db.session.commit()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# @app.route("/qr/shop/<shop_id>")
# def get_qr_shop_image(shop_id):
#     logger.info("Serving generated Shop QR images", shop_id=shop_id)
#     img_buf = io.BytesIO()
#     url = f"{app.config['FRONTEND_URI']}/shop/{shop_id}"
#     logger.debug("Shop QR URL", url=url)
#     img = generate_qr_image(url=url)
#     img.save(img_buf)
#     img_buf.seek(0)
#     return flask.send_file(img_buf, mimetype="image/png")


T = TypeVar("T")
ResponseHeaders = Dict[str, str]
Response = Union[T, Tuple[T, HTTPStatus], Tuple[T, HTTPStatus, ResponseHeaders]]
ErrorState = Union[str, Exception, Tuple[str, Union[int, HTTPStatus]]]
ErrorDict = Dict[str, Union[str, int, List[Dict[str, Any]], "InputForm", None]]


# Todo: move this to Flask example?
def json_endpoint(f: Callable[..., Union[JSON, Response[JSON]]]) -> Callable[..., Union[str, Response[str]]]:
    @wraps(f)
    def to_json(*args: Any, **kwargs: Any) -> Union[str, Tuple[str, HTTPStatus]]:
        result = f(*args, **kwargs)
        if isinstance(result, tuple):
            body, status = result
            return jsonify(body), status
        return jsonify(result)

    return to_json


class ApiException(Exception):
    """Api Exception Class.

    This is a copy of what is generated in api_clients. We use this to have consistent error handling for nso to.
    This should conform to what is used in the api clients.
    """

    status: Optional[HTTPStatus]
    reason: Optional[str]
    body: Optional[str]
    headers: Dict[str, str]

    def __init__(
        self, status: Optional[HTTPStatus] = None, reason: Optional[str] = None, http_resp: Optional[object] = None
    ):
        super().__init__(status, reason, http_resp)
        if http_resp:
            self.status = http_resp.status  # type:ignore
            self.reason = http_resp.reason  # type:ignore
            self.body = http_resp.data  # type:ignore
            self.headers = http_resp.getheaders()  # type:ignore
        else:
            self.status = status
            self.reason = reason
            self.body = None
            self.headers = {}

    def __str__(self) -> str:
        """Create custom error messages for exception."""
        error_message = "({})\n" "Reason: {}\n".format(self.status, self.reason)
        if self.headers:
            error_message += f"HTTP response headers: {self.headers}\n"

        if self.body:
            error_message += f"HTTP response body: {self.body}\n"

        return error_message


def show_ex(ex: Exception, stacklimit: Optional[int] = None) -> str:
    """
    Show an exception, including its class name, message and (limited) stacktrace.

    >>> try:
    ...     raise Exception("Something went wrong")
    ... except Exception as e:
    ...     print(show_ex(e))
    Exception: Something went wrong
    ...
    """
    tbfmt = "".join(traceback.format_tb(ex.__traceback__, stacklimit))
    return "{}: {}\n{}".format(type(ex).__name__, ex, tbfmt)


def error_state_to_dict(err: ErrorState) -> ErrorDict:
    """Return an ErrorDict based on the exception, string or tuple in the ErrorState.

    Args:
        err: ErrorState from a workflow or api error state

    Returns:
        An ErrorDict containing the error message a status_code and a traceback if available

    """
    if isinstance(err, FormValidationError):
        return {
            "class": type(err).__name__,
            "error": str(err),
            "traceback": show_ex(err),
            "validation_errors": err.errors,  # type:ignore
            "status_code": HTTPStatus.BAD_REQUEST,
        }
    elif isinstance(err, FormNotCompleteError):
        return {
            "class": type(err).__name__,
            "error": str(err),
            "traceback": show_ex(err),
            "form": err.form,
            "status_code": HTTPStatus.NOT_EXTENDED,
        }
    elif isinstance(err, Exception):
        if is_api_exception(err):
            err = cast(ApiException, err)
            return {
                "class": type(err).__name__,
                "error": err.reason,
                "status_code": err.status,
                "body": err.body,
                "headers": "\n".join(f"{k}: {v}" for k, v in err.headers.items()),
                "traceback": show_ex(err),
            }
        return {"class": type(err).__name__, "error": str(err), "traceback": show_ex(err)}
    elif isinstance(err, tuple):
        cast(Tuple, err)
        error, status_code = err
        return {"error": str(error), "status_code": int(status_code)}
    elif isinstance(err, str):
        return {"error": err}
    elif isinstance(err, dict) and "error" in err:  # type: ignore
        return err
    else:
        raise TypeError("ErrorState  should be a tuple, exception or string")


def is_api_exception(ex: Exception) -> bool:
    """Test for swagger-codegen ApiException.

    For each API, swagger-codegen generates a new ApiException class. These are not organized into
    a hierarchy. Hence testing whether one is dealing with one of the ApiException classes without knowing how
    many there are and where they are located, needs some special logic.

    Args:
        ex: the Exception to be tested.

    Returns:
        True if it is an ApiException, False otherwise.

    """
    return ex.__class__.__name__ == "ApiException"


def show_error(err: ErrorState) -> Response[ErrorDict]:
    error_dict = error_state_to_dict(err)
    # logger.error("Returning error dict", **error_dict)
    status_code: HTTPStatus = error_dict.pop("status_code", HTTPStatus.INTERNAL_SERVER_ERROR)  # type: ignore
    return error_dict, status_code


def _get_json() -> JSON:
    if request.is_json:
        return request.get_json()
    else:
        raise ValueError("No JSON")


@app.route("/forms/<form_key>", methods=["POST"])
# @json_endpoint
def new_form(form_key):
    logger.info("New form")
    json_data = _get_json()

    if form_key in list_forms():
        try:
            state = start_form(form_key, user_inputs=json_data, user="Just a user")
        except (FormValidationError, FormNotCompleteError) as e:
            return show_error(e)
        return state, 201
    return None, 440


@app.route("/qr/shop/<shop_id>/<table_id>")
def get_qr_shop_table_image(shop_id, table_id):
    logger.info("Serving generated Shop/Table QR images", shop_id=shop_id, table_id=table_id)
    img_buf = io.BytesIO()
    url = f"{app.config['FRONTEND_URI']}/shop/{shop_id}/{table_id}"
    logger.debug("Shop QR URL", url=url)
    img = generate_qr_image(url=url)
    img.save(img_buf)
    img_buf.seek(0)
    return flask.send_file(img_buf, mimetype="image/png")


@app.route("/qr/shop/<shop_id>/category/<category_id>")
def get_qr_category_image(shop_id, category_id):
    logger.info("Serving generated Category QR images", shop_id=shop_id, category_id=category_id)
    img_buf = io.BytesIO()
    url = f"{app.config['FRONTEND_URI']}/shop/{shop_id}/category/{category_id}"
    logger.debug("Category QR URL", url=url)
    img = generate_qr_image(url=url)
    img.save(img_buf)
    img_buf.seek(0)
    return flask.send_file(img_buf, mimetype="image/png")


@app.route("/qr/shop/<shop_id>/category/<category_id>/product/<product_id>")
def get_qr_product_image(shop_id, category_id, product_id):
    logger.info("Serving generated Product QR images", shop_id=shop_id, category_id=category_id, product_id=product_id)
    img_buf = io.BytesIO()
    url = f"{app.config['FRONTEND_URI']}/shop/{shop_id}/category/{category_id}/product/{product_id}"
    logger.debug("Product QR URL", url=url)
    img = generate_qr_image(url=url)
    img.save(img_buf)
    img_buf.seek(0)
    return flask.send_file(img_buf, mimetype="image/png")


@app.route("/get_my_ip", methods=["GET"])
def get_my_ip():
    return jsonify({"ip": request.remote_addr, "alt": request.access_route[0]}), 200


# @app.before_request
# def log_request_info():
#     app.logger.debug("Headers: %s", request.headers)
#     app.logger.debug("Body: %s", request.get_data())


# Views
api.init_app(app)
db.init_app(app)
mail.init_app(app)
admin.add_view(ShopAdminView(Shop, db.session))
admin.add_view(OrderAdminView(Order, db.session))
admin.add_view(BaseAdminView(MainCategory, db.session))
admin.add_view(CategoryAdminView(Category, db.session))
admin.add_view(KindAdminView(Kind, db.session))
admin.add_view(PriceAdminView(Price, db.session))
admin.add_view(UserAdminView(User, db.session))
admin.add_view(RolesAdminView(Role, db.session))
admin.add_view(BaseAdminView(Tag, db.session))
admin.add_view(BaseAdminView(Flavor, db.session))
admin.add_view(BaseAdminView(KindToTag, db.session))
admin.add_view(BaseAdminView(KindToFlavor, db.session))
admin.add_view(BaseAdminView(ShopToPrice, db.session))

migrate = Migrate(app, db)
logger.info("Ready loading admin views and api")

if __name__ == "__main__":
    app.run()
