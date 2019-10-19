import datetime
import uuid

from flask_security import RoleMixin, SQLAlchemySessionUserDatastore, UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref, relationship

db = SQLAlchemy()


class RolesUsers(db.Model):
    __tablename__ = "roles_users"
    id = Column(Integer(), primary_key=True)
    user_id = Column("user_id", UUID(as_uuid=True), ForeignKey("user.id"))
    role_id = Column("role_id", UUID(as_uuid=True), ForeignKey("role.id"))


class Role(db.Model, RoleMixin):
    __tablename__ = "role"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(80), unique=True)
    description = Column(String(255))

    # __str__ is required by Flask-Admin, so we can have human-readable values for the Role when editing a User.
    def __str__(self):
        return self.name

    # __hash__ is required to avoid the exception TypeError: unhashable type: 'Role' when saving a User
    def __hash__(self):
        return hash(self.name)


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True)
    first_name = Column(String(255), index=True)
    last_name = Column(String(255), index=True)
    username = Column(String(255), unique=True)
    password = Column(String(255))
    active = Column(Boolean())
    fs_uniquifier = Column(String(255))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    confirmed_at = Column(DateTime())
    roles = relationship("Role", secondary="roles_users", backref=backref("users", lazy="dynamic"))

    mail_offers = Column(Boolean, default=False)

    # Human-readable values for the User when editing user related stuff.
    def __str__(self):
        return f"{self.username} : {self.email}"

    # __hash__ is required to avoid the exception TypeError: unhashable type: 'Role' when saving a User
    def __hash__(self):
        return hash(self.email)


class Tag(db.Model):
    __tablename__ = "tags"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(60), unique=True, index=True)

    def __repr__(self):
        return self.name


class Flavor(db.Model):
    __tablename__ = "flavors"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(60), unique=True, index=True)
    icon = Column(String(60), unique=True, index=True)
    color = Column(String(20), default="#000000")

    def __repr__(self):
        return self.name


class Shop(db.Model):
    __tablename__ = "shops"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), unique=True, index=True)
    description = Column(String(255), unique=True)

    def __repr__(self):
        return self.name


class Category(db.Model):
    __tablename__ = "categories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255))
    description = Column(String(255), unique=True, index=True)
    shop_id = Column("shop_id", UUID(as_uuid=True), ForeignKey("shops.id"), index=True)
    shop = db.relationship("Shop", lazy=True)

    def __repr__(self):
        return f"{self.shop.name}: {self.name}"


class Kind(db.Model):
    __tablename__ = "kinds"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), unique=True, index=True)
    short_description_nl = Column(String())
    description_nl = Column(String())
    short_description_en = Column(String())
    description_en = Column(String())
    c = Column(Boolean(), default=False)
    h = Column(Boolean(), default=False)
    i = Column(Boolean(), default=False)
    s = Column(Boolean(), default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    kind_tags = relationship("Tag", secondary="kinds_to_tags")
    kind_to_tags = relationship("KindToTag")
    kind_flavors = relationship("Flavor", secondary="kinds_to_flavors")
    kind_to_flavors = relationship("KindToFlavor")

    def __repr__(self):
        return "<Kinds %r, id:%s>" % (self.name, self.id)


class Price(db.Model):
    __tablename__ = "prices"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    internal_product_id = Column("internal_product_id", String(), unique=True)
    half = Column("half", Float(), nullable=True)
    one = Column("one", Float(), nullable=True)
    two_five = Column("two_five", Float(), nullable=True)
    five = Column("five", Float(), nullable=True)
    joint = Column("joint", Float(), nullable=True)
    piece = Column("piece", Float(), nullable=True)

    def __repr__(self):
        return f"Price for product_id: {self.internal_product_id}"


# Tag many to many relations
class KindToTag(db.Model):
    __tablename__ = "kinds_to_tags"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    amount = Column("amount", Integer(), default=0)
    kind_id = Column("kind_id", UUID(as_uuid=True), ForeignKey("kinds.id"), index=True)
    tag_id = Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id"), index=True)
    kind = db.relationship("Kind", lazy=True)
    tag = db.relationship("Tag", lazy=True)


# Flavor many to many relation
class KindToFlavor(db.Model):
    __tablename__ = "kinds_to_flavors"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    kind_id = Column("kind_id", UUID(as_uuid=True), ForeignKey("kinds.id"), index=True)
    flavor_id = Column("flavor_id", UUID(as_uuid=True), ForeignKey("flavors.id"), index=True)
    kind = db.relationship("Kind", lazy=True)
    flavor = db.relationship("Flavor", lazy=True)

    def __repr__(self):
        return f"{self.flavor.name}: {self.kind.name}"


class ShopToPrice(db.Model):
    __tablename__ = "shops_to_price"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    active = Column("active", Boolean(), default=True)
    shop_id = Column("shop_id", UUID(as_uuid=True), ForeignKey("shops.id"), index=True)
    shop = db.relationship("Shop", lazy=True)
    category_id = Column("category_id", UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True, index=True)
    category = db.relationship("Category", lazy=True)
    kind_id = Column("kind_id", UUID(as_uuid=True), ForeignKey("kinds.id"), index=True)
    kind = db.relationship("Kind", lazy=True)
    price_id = Column("price_id", UUID(as_uuid=True), ForeignKey("prices.id"), index=True)
    price = db.relationship("Price", lazy=True)
    use_half = Column("use_half", Boolean(), default=True)
    use_one = Column("use_one", Boolean(), default=True)
    use_two_five = Column("two_five", Boolean(), default=True)
    use_five = Column("use_five", Boolean(), default=True)
    use_joint = Column("use_joint", Boolean(), default=True)
    use_piece = Column("use_piece", Boolean(), default=True)


user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
