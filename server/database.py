import hashlib
import sqlalchemy

import datetime
import uuid

from flask_security import RoleMixin, UserMixin, SQLAlchemySessionUserDatastore
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref

db = SQLAlchemy()


class RolesUsers(db.Model):
    __tablename__ = 'roles_users'
    id = Column(Integer(), primary_key=True)
    user_id = Column('user_id', UUID(as_uuid=True), ForeignKey('user.id'))
    role_id = Column('role_id', UUID(as_uuid=True), ForeignKey('role.id'))


class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
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
    __tablename__ = 'user'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True)
    first_name = Column(String(255), index=True)
    last_name = Column(String(255), index=True)
    username = Column(String(255), unique=True)
    password = Column(String(255))
    active = Column(Boolean())
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    confirmed_at = Column(DateTime())
    roles = relationship('Role', secondary='roles_users', backref=backref('users', lazy='dynamic'))

    mail_offers = Column(Boolean, default=False)

    # Human-readable values for the User when editing user related stuff.
    def __str__(self):
        return f'{self.username} : {self.email}'

    # __hash__ is required to avoid the exception TypeError: unhashable type: 'Role' when saving a User
    def __hash__(self):
        return hash(self.email)


class Tag(db.Model):
    __tablename__ = 'tags'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(60), unique=True, index=True)

    def __repr__(self):
        return self.name


class Category(db.Model):
    __tablename__ = 'categories'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), unique=True, index=True)
    description = Column(String(255), unique=True, index=True)
    category_shops = relationship("Shop", secondary='shop_categories')

    def __repr__(self):
        return self.name


class Shop(db.Model):
    __tablename__ = 'shops'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), unique=True, index=True)
    description = Column(String(255), unique=True, index=True)

    def __repr__(self):
        return self.name


class ShopCategory(db.Model):
    __tablename__ = 'shop_categories'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    category_id = Column('item_id', UUID(as_uuid=True), ForeignKey('categories.id'), index=True)
    shop_id = Column('shop_id', UUID(as_uuid=True), ForeignKey('shops.id'), index=True)
    category = db.relationship("Category", lazy=True)
    shop = db.relationship("Shop", lazy=True)

    def __repr__(self):
        # add shop also?
        return self.category.name


class Item(db.Model):
    __tablename__ = 'items'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), unique=True, index=True)
    description = Column(String())
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    price = Column(Float, nullable=True)
    item_tags = relationship("Tag", secondary='item_tags')
    category_id = Column('category_id', UUID(as_uuid=True), ForeignKey('categories.id'))
    category = relationship("Category")

    def __repr__(self):
        return '<Item %r, id:%s>' % (self.name, self.id)


# Setup tagging for all resources that need it
class ItemTag(db.Model):
    __tablename__ = 'item_tags'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    amount = Column('amount', Integer(), nullable=True)
    item_id = Column('item_id', UUID(as_uuid=True), ForeignKey('items.id'), index=True)
    tag_id = Column('tag_id', UUID(as_uuid=True), ForeignKey('tags.id'), index=True)
    item = db.relationship("Item", lazy=True)
    tag = db.relationship("Tag", lazy=True)

    def __repr__(self):
        print(self.tag)
        return self.tag.name


user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
