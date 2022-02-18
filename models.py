from flask_user import UserMixin
from .app import db
from datetime import datetime


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

    # User authentication information. The collation='NOCASE' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
    email = db.Column(db.String(255, collation='C'), nullable=False, unique=True, index=True)
    email_confirmed_at = db.Column(db.DateTime())
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)
    # username = db.Column(db.String(255, collation='C'), nullable=True, unique=True, server_default=None)
    password = db.Column(db.String(255), nullable=False, server_default='')

    # User information
    first_name = db.Column(db.String(100, collation='C'), nullable=False, server_default='')
    last_name = db.Column(db.String(100, collation='C'), nullable=False, server_default='')

    # Define the relationship to Role via UserRoles
    roles = db.relationship('Role', secondary='user_roles')


# Define the Role data-model
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, default="")


# Define the UserRoles association table
class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))


class Token(db.Model):
    __tablename__ = 'tokens'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'), index=True)
    token = db.Column(db.String(256), unique=True, nullable=False, default="")


class Stats(db.Model):
    __tablename__ = 'stats'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'), index=True)
    pins_added = db.Column(db.Integer(), default=0)
    last_pin_at = db.Column(db.DateTime(), server_default=None)
    pinterest_requests_left = db.Column(db.Integer(), default=0)


class PinData(db.Model):
    __tablename__ = 'pin_data'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'), index=True)
    source_board = db.Column(db.String(2000), index=True, nullable=False, default="")
    destination_board = db.Column(db.String(300), index=True, nullable=False, default="")
    bookmark = db.Column(db.Integer(), default=0)


class PinterestData(db.Model):
    __tablename__ = 'pinterest_data'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'), index=True)
    username = db.Column(db.String(300), nullable=False, default="")


class IPDetails(db.Model):
    __tablename__ = 'ip_details'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'), index=True)
    ip_address = db.Column(db.String(300), nullable=False, default="")


class Payments(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'), index=True)
    amount_received = db.Column(db.Integer(), default=0)
    currency = db.Column(db.String(3), nullable=False, default="")
    pins_bought = db.Column(db.Integer(), default=0)
    stripe_session_id = db.Column(db.String(300), nullable=False, default="")