import os
import requests
import urllib.parse
from flask_user import UserManager
from flask import session
from datetime import datetime
from app import app, db
from flask_user import current_user

from models import User, Token, PinterestData, PinData, Stats

# Setup Flask-User and specify the User data-model
user_manager = UserManager(app, db, User)

PINTEREST_CLIENT_ID = os.environ.get("PINTEREST_CLIENT_ID")
PINTEREST_API_BASE_URL = os.environ.get("PINTEREST_API_BASE_URL")
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
    token_url = PINTEREST_API_BASE_URL + "/oauth/token?" + url_params
    r = requests.post(token_url)
    response = r.json()
    access_token = response["access_token"]

    return access_token


def save_token_to_database(token):
    if not Token.query.filter_by(user_id=current_user.id).first():
        token = Token(
            user_id=current_user.id,
            token=token,
        )
        db.session.add(token)
    else:
        token_instance = Token.query.filter_by(user_id=current_user.id).first()
        token_instance.token = token

    db.session.commit()
    return token


def save_profile_and_return_requests_left():
    params = {
        "access_token": session['pa-token'],
        "fields": "id,username,first_name,last_name,counts"
    }

    url_params = urllib.parse.urlencode(params)
    url = PINTEREST_API_BASE_URL + '/me?' + url_params
    r = requests.get(url, params)
    res = r.json()
    res = res["data"]

    if not PinterestData.query.filter_by(user_id=current_user.id).first():
        pinterest_data = PinterestData(
            user_id=current_user.id,
            pinterest_id=res["id"],
            username=res["username"],
            first_name=res["first_name"],
            last_name=res["last_name"],
            pins=res["counts"]["pins"],
            boards=res["counts"]["boards"],
            followers=res["counts"]["followers"],
            following=res["counts"]["following"],
        )
        db.session.add(pinterest_data)
    else:
        pinterest_data_instance = PinterestData.query.filter_by(user_id=current_user.id).first()
        pinterest_data_instance.username = res["username"]
        pinterest_data_instance.pins = res["counts"]["pins"]
        pinterest_data_instance.boards = res["counts"]["boards"]
        pinterest_data_instance.followers = res["counts"]["followers"]
        pinterest_data_instance.following = res["counts"]["following"]

    db.session.commit()

    return r.headers['X-RateLimit-Remaining']


def get_last_pin_details(source, destination):
    pin_data = PinData.query.filter_by(user_id=current_user.id, source_board=source, destination_board=destination).first()

    data = None

    if pin_data:
        data = {
            "pins_copied": pin_data.pins_copied,
            "cursor": pin_data.cursor
        }

    return data


def update_pin_data(source, destination, pins_added, last_cursor):
    if not PinData.query.filter_by(user_id=current_user.id, source_board=source, destination_board=destination).first():
        pin_data = PinData(
            user_id=current_user.id,
            source_board=source,
            destination_board=destination,
            pins_copied=pins_added,
            cursor=last_cursor
        )
        db.session.add(pin_data)
    else:
        pin_data_instance = PinData.query.filter_by(user_id=current_user.id, source_board=source, destination_board=destination).first()
        pin_data_instance.pins_copied += pins_added
        pin_data_instance.cursor = last_cursor

    db.session.commit()
    return True


def update_stats(pin_added):
    if not Stats.query.filter_by(user_id=current_user.id).first():
        stats = Stats(
            user_id=current_user.id,
            total_pins=pin_added,
            last_pin_at=datetime.utcnow()
        )
        db.session.add(stats)
    else:
        stats_instance = Stats.query.filter_by(user_id=current_user.id).first()
        stats_instance.total_pins += pin_added
        stats_instance.last_pin_at = datetime.utcnow()

    db.session.commit()
    return True


def get_next_pins(source, num, cont, cursor):
    remainder = int(num) % 100
    remainder = remainder if int(num)/100 == 0 else (remainder + 1)

    all_pins = []

    params = {
        "access_token": session['pa-token'],
        "limit": 2,
    }
    if cont == "true":
        params["cursor"] = cursor

    for x in range(1):
        session['status'] = "Fetching Pins: " + str(x*100)
        url_params = urllib.parse.urlencode(params)
        url = PINTEREST_API_BASE_URL + "/boards/{}/pins?{}&fields=id,link,url,note,image".format(source, url_params)
        r = requests.get(url)

        if r.status_code == 200:
            res = r.json()
            all_pins = all_pins + res["data"]
            params["cursor"] = res["page"]["cursor"]
            return all_pins
        else:
            raise Exception()


def save_pins(pins, destination):
    counter = 0
    for pin in pins:
        url = PINTEREST_API_BASE_URL + '/pins/?access_token=' + session['pa-token'] + "&fields=id"

        post_data = {
            "board": destination,
            "note": pin["note"],
            # "link": pin["link"],      Adding links is not feasible as these are
            #                           Pinterest Links and Pinterest API doesn't
            #                           allow adding them.
            "image_url": pin["image"]["original"]["url"]
        }

        r = requests.post(url, data=post_data)

        if r.status_code != 201:
            return False

        counter = counter + 1
        session['status'] = "Pins added: " + str(counter)

    if "page" in pins[-1]:
        last_cursor = pins[-1]["page"]["cursor"]
    else:
        last_cursor = ""

    del pins

    res = {
        "last_cursor": last_cursor,
        "pins_added": counter
    }

    return res
