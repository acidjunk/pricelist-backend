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


class Shop(db.Model):
    __tablename__ = "shops"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), unique=True, index=True)
    description = Column(String(255), unique=True, index=True)

    def __repr__(self):
        return self.name


class Kind(db.Model):
    __tablename__ = "kinds"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), unique=True, index=True)
    short_description_nl = Column(String())
    description_nl = Column(String())
    short_description_en = Column(String())
    description_en = Column(String())
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    product_tags = relationship("Tag", secondary="kinds_to_tags")
    product_to_tags = relationship("KindToTag")

    def __repr__(self):
        return "<Kinds %r, id:%s>" % (self.name, self.id)


class Price(db.Model):
    __tablename__ = "prices"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    internal_product_id = Column(String(255), nullable=True)
    half = Column("half", Float(), nullable=True)
    one = Column("one", Float(), nullable=True)
    five = Column("five", Float(), nullable=True)
    joint = Column("joint", Float(), nullable=True)


# Setup tagging for all resources that need it
class KindToTag(db.Model):
    __tablename__ = "kinds_to_tags"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    amount = Column("amount", Integer(), default=0)
    kind_id = Column("kind_id", UUID(as_uuid=True), ForeignKey("kinds.id"), index=True)
    tag_id = Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id"), index=True)
    kind = db.relationship("Kind", lazy=True)
    tag = db.relationship("Tag", lazy=True)

    def __repr__(self):
        return f"{self.tag.name}: {self.amount}%"


user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
