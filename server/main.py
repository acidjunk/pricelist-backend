import io
import os

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
from flask import Flask, url_for, jsonify, request
from flask_admin import Admin
from flask_admin import helpers as admin_helpers
from flask_cors import CORS
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_security import Security, user_registered
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


#
# @login_manager.request_loader
# def load_user_from_request(request):
#
#
#
#     token = request.headers.get('Authentication-Token')
#     data = verify_auth_token(token, "login" )
#     print(data)
#
#
#     # if token:
#     #     user_id = User.decode_token(token)
#     #     print(user_id)
#     #     1/0
#
#     # finally, return None if both methods did not login the user
#     return None


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route("/qr/shop/<shop_id>")
def get_qr_shop_image(shop_id):
    logger.info("Serving generated Shop QR images", shop_id=shop_id)
    img_buf = io.BytesIO()
    url = f"{app.config['FRONTEND_URI']}/shop/{shop_id}"
    logger.debug("Shop QR URL", url=url)
    img = generate_qr_image(url=url)
    img.save(img_buf)
    img_buf.seek(0)
    return flask.send_file(img_buf, mimetype="image/png")


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
