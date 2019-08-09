import os
import requests
import urllib.parse
from flask_user import UserManager
from flask import session, abort, request
from datetime import datetime
from app import app, db
from flask_user import current_user

from models import User, Token, PinterestData, PinData, Stats, IPDetails

# Setup Flask-User and specify the User data-model
user_manager = UserManager(app, db, User)

PINTEREST_CLIENT_ID = os.environ.get("PINTEREST_CLIENT_ID")
PINTEREST_API_BASE_URL = os.environ.get("PINTEREST_API_BASE_URL")
PINTEREST_CLIENT_SECRET = os.environ.get("PINTEREST_CLIENT_SECRET")


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
    if r.status_code == 200:
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
        return {"data": r.headers['X-RateLimit-Remaining'], "code": 200}
    elif r.status_code == 401:
        return {"data": "Access token invalid.", "code": 401}


def save_ip():
    ip_address = str(request.remote_addr)

    if not IPDetails.query.filter_by(user_id=current_user.id, ip_address=ip_address).first():
        ip_details = IPDetails(
            user_id=current_user.id,
            ip_address=ip_address,
        )
        db.session.add(ip_details)
        db.session.commit()

        return True


def get_last_pin_details(source, destination):
    pin_data = PinData.query.filter_by(user_id=current_user.id, source_board=source, destination_board=destination).first()

    data = None

    if pin_data:
        data = {
            "pins_copied": pin_data.pins_copied,
            "cursor": pin_data.cursor
        }

    return data


def update_pin_data(source, destination, pins_added, last_cursor, current_user_id):
    if not PinData.query.filter_by(user_id=current_user_id, source_board=source, destination_board=destination).first():
        pin_data = PinData(
            user_id=current_user_id,
            source_board=source,
            destination_board=destination,
            pins_copied=pins_added,
            cursor=last_cursor,
        )
        db.session.add(pin_data)
    else:
        pin_data_instance = PinData.query.filter_by(user_id=current_user_id, source_board=source, destination_board=destination).first()
        pin_data_instance.pins_copied += pins_added
        pin_data_instance.cursor = last_cursor

    db.session.commit()
    return True


def update_stats(pin_added, current_user_id):
    if not Stats.query.filter_by(user_id=current_user_id).first():
        stats = Stats(
            user_id=current_user_id,
            total_pins=pin_added,
            last_pin_at=datetime.utcnow()
        )
        db.session.add(stats)
    else:
        stats_instance = Stats.query.filter_by(user_id=current_user_id).first()
        stats_instance.total_pins += pin_added
        stats_instance.last_pin_at = datetime.utcnow()

    db.session.commit()
    return True


def get_next_pins(source, num, cont, cursor):
    remainder = int(int(num) / 100)
    remainder = remainder if int(int(num) % 100) == 0 else (remainder + 1)

    print("Remainder = " + str(remainder))

    all_pins = []

    params = {
        "access_token": session['pa-token'],
        "limit": 100,
    }
    if cont == "true":
        params["cursor"] = cursor

    for x in range(remainder):
        session['status'] = "Fetching Pins: " + str(x*100)
        url_params = urllib.parse.urlencode(params)
        url = PINTEREST_API_BASE_URL + "/boards/{}/pins?{}&fields=note,image".format(source, url_params)
        r = requests.get(url)

        print(url)

        print(r.status_code)

        if r.status_code == 200:
            res = r.json()
            all_pins = all_pins + res["data"]

            if res["page"]["cursor"] != None:
                params["cursor"] = res["page"]["cursor"]
            else:
                # If requests left > number of pins in the source board
                params["cursor"] = ""
                break
        else:
            print(r.json())
            abort(500)

    response = {
        "all_pins": all_pins,
        "last_cursor": params["cursor"]
    }

    return response
