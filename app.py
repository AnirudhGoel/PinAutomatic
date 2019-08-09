import os
from flask import Flask, render_template, session, request, redirect, url_for, flash, jsonify, abort
from flask_babelex import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_user import current_user, login_required
from config import ConfigClass
import urllib.parse as urlparse


app = Flask(__name__)
app.config.from_object(ConfigClass)


db = SQLAlchemy(app)
babel = Babel(app)
from services import get_token, save_token_to_database, get_next_pins, save_profile_and_return_requests_left, get_last_pin_details, save_pins, update_pin_data, update_stats

# Create all database tables and create admin
# db.create_all()
# create_admin_if_not_exists()

PINTEREST_CLIENT_ID = os.environ.get("PINTEREST_CLIENT_ID")


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    else:
        return redirect('/user/sign-in')


@app.route('/home')
@login_required
def home():
    credentials = {
        'client_id': PINTEREST_CLIENT_ID
    }

    if 'pa-token' in session:
        session['status'] = ""
        return render_template('index.html', title='Home')
    else:
        return render_template('authorize.html', title='Login', credentials=credentials)

@app.route('/pinterest-auth')
@login_required
def pinterest_auth():
    if request.args.get('state', None) == "secret":
        if request.args.get('code', None):
            temp_code = request.args.get('code', None)
            access_token = get_token(temp_code)
            save_token_to_database(access_token)

            session['pa-token'] = access_token

            return redirect(url_for('index'))
        else:
            flash("You need to provide authorization to PinterestAutomatic to allow adding of pins to your board.", category='error')
            return redirect(url_for('home'))
    else:
        return redirect('/user/sign-out')

@app.route('/pin-it')
@login_required
def pin_it():
    session['status'] = ""

    parsed = urlparse.urlparse(request.url)
    source = urlparse.parse_qs(parsed.query)['source'][0]
    destination = urlparse.parse_qs(parsed.query)['destination'][0]
    requests_left = urlparse.parse_qs(parsed.query)['requests_left'][0]
    cont = urlparse.parse_qs(parsed.query)['cont'][0]
    cursor = urlparse.parse_qs(parsed.query)['cursor'][0]

    try:
        r = get_next_pins(source, requests_left, cont, cursor)
        all_pins = r["all_pins"]
        last_cursor = r["last_cursor"]
    except:
        abort(400)

    try:
        res = save_pins(all_pins, destination, last_cursor)
    except:
        abort(400)

    update_pin_data(source, destination, res["pins_added"], res["last_cursor"])
    update_stats(res["pins_added"])

    response = {
        "data": str(res["pins_added"]) + " pins(s) added successfully.",
        "code": 200
    }
    return jsonify(response)


@app.route('/get-requests-left')
@login_required
def get_requests_left():
    requests_left = save_profile_and_return_requests_left()
    session["req_left"] = requests_left
    return requests_left


@app.route('/check-last-pin-status')
@login_required
def check_last_pin_status():
    parsed = urlparse.urlparse(request.url)
    source = urlparse.parse_qs(parsed.query)['source'][0]
    destination = urlparse.parse_qs(parsed.query)['destination'][0]
    last_pin_details = get_last_pin_details(source, destination)
    res = {
        "code": 404
    }

    if last_pin_details:
        res = {
            "code": 200,
            "pins_copied": last_pin_details['pins_copied'],
            "cursor": last_pin_details['cursor']
        }

    return res


@app.route('/check-session-status')
@login_required
def check_session_status():
    session_status = {
        "status": session["status"],
        "requests_left": session["req_left"]
    }
    return session_status


# # The Admin page requires an 'Admin' role.
# @app.route('/admin')
# @roles_required('Admin')    # Use of @roles_required decorator
# def admin_page():
#     pass
