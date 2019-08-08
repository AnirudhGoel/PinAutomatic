import os
import requests
import urllib.parse
from flask_user import UserManager
from datetime import datetime
from app import app, db
from flask_user import current_user

from models import User, Role, Token

# Setup Flask-User and specify the User data-model
user_manager = UserManager(app, db, User)

PINTEREST_CLIENT_ID = os.environ.get("PINTEREST_CLIENT_ID")
PINTEREST_TOKEN_URL = os.environ.get("PINTEREST_TOKEN_URL")
PINTEREST_CLIENT_SECRET = os.environ.get("PINTEREST_CLIENT_SECRET")


# def create_admin_if_not_exists():
#     # Create 'admin@example.com' user with 'Admin' role
#     if not User.query.filter(User.email == 'admin@example.com').first():
#         user = User(
#             email='admin@example.com',
#             email_confirmed_at=datetime.utcnow(),
#             password=user_manager.hash_password('yankring'),
#         )
#         user.roles.append(Role(name='Admin'))
#         db.session.add(user)
#         db.session.commit()


def get_token(temp_code):
    params = {
        "grant_type": "authorization_code",
        "client_id": PINTEREST_CLIENT_ID,
        "client_secret": PINTEREST_CLIENT_SECRET,
        "code": temp_code
    }

    url_params = urllib.parse.urlencode(params)
    token_url = PINTEREST_TOKEN_URL + "?" + url_params
    r = requests.post(token_url)
    response = r.json()
    access_token = response["access_token"]

    return access_token


def save_token_to_database(token):
    if not User.query.filter_by(email=current_user.email).first():
        token = Token(
            user_id=current_user.id,
            token=token,
        )
        db.session.add(token)
        db.session.commit()
