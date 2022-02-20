import hashlib
import os
import time
import json
import urllib.parse as urlparse

import requests
import stripe
from flask import (Flask, abort, flash, jsonify, redirect, render_template,
                   request, session, url_for)
from flask_babelex import Babel
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_user import current_user, login_required
from rq import Queue
from rq.job import Job

from config import ConfigClass
from worker import conn

app = Flask(__name__)
app.config.from_object(ConfigClass)

q = Queue(connection=conn, default_timeout=1200)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
babel = Babel(app)
from models import User
from services import (get_board_id, get_images, get_last_pin_details,
                      get_pins_added, get_pins_available_from_subscription,
                      get_pinterest_requests_left, get_token,
                      get_total_pins_from_subscription, save_ip,
                      save_stripe_session_id, save_token_to_database,
                      update_payment, update_pin_data,
                      update_pinterest_profile, update_pinterest_requests_left,
                      update_stats)

# Create all database tables and create admin
# db.create_all()
# create_admin_if_not_exists()

PINTEREST_CLIENT_ID = os.environ.get("PINTEREST_CLIENT_ID")
PINTEREST_API_BASE_URL = os.environ.get("PINTEREST_API_BASE_URL")
SITE_SCHEME = os.environ.get("SITE_SCHEME", default="https")
SITE_DOMAIN = os.environ.get("SITE_DOMAIN", default="pinautomatic.herokuapp.com")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")

stripe.api_key = STRIPE_SECRET_KEY

@app.route('/')
def index():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	else:
		return redirect('/user/sign-in')


@app.route('/privacy-policy')
def privacy_policy():
	return render_template('privacy_policy.html')


@app.route('/home')
@login_required
def home():
	credentials = {
		'client_id': PINTEREST_CLIENT_ID,
		'redirect_uri': SITE_SCHEME + "://" + SITE_DOMAIN,
		'state': hashlib.sha256(os.urandom(1024)).hexdigest(),
		'scope': 'boards:read,boards:read_secret,boards:write,boards:write_secret,pins:read,pins:write,pins:write_secret,user_accounts:read'
	}
	session['state'] = credentials['state']

	if 'pa-token' in session:  # User logged in and authorized via Pinterest
		r = update_pinterest_profile()
		if r['code'] == 200:
			username = r['username']
			data = {
				'username': username
			}
		elif r['code'] == 401:
			session.pop('pa-token')
			return redirect('/user/sign-out')

		update_pinterest_requests_left()

		data['total_pins_bought'] = get_total_pins_from_subscription()
		data['pins_added'] = get_pins_added()
		save_ip()
		return render_template('index.html', title='Home', data=data)
	else:  # User not authorized via Pinterest
		return render_template('authorize.html', title='Login', credentials=credentials)


@app.route('/pinterest-auth')
@login_required
def pinterest_auth():
	if request.args.get('state', None) == session['state']:
		if request.args.get('code', None):
			temp_code = request.args.get('code', None)

			# As per new API docs, this redirect_uri just needs to be passed. Should be one from the authorized redirect_uris
			redirect_uri = SITE_SCHEME + "://" + SITE_DOMAIN + '/pinterest-auth'
			access_token = get_token(temp_code, redirect_uri)
			save_token_to_database(access_token)

			session['pa-token'] = access_token

			return redirect(url_for('index'))
		else:
			flash("You need to provide authorization to PinAutomatic to allow adding of pins to your board.", category='error')
			return redirect(url_for('home'))
	else:
		return redirect('/user/sign-out')


@app.route('/pin-it', methods=['POST'])
@login_required
def pin_it():
	if not check_user_active():
		return jsonify({"code": 401, "data": "/user/sign-out"})

	data = request.json

	source_url = data['source']
	destination = data['destination']
	requests_left = get_pinterest_requests_left()
	cont = data['cont']
	pin_link = data['pin_link'] if data['pin_link'] else 'https://pinautomatic.herokuapp.com'
	pin_title = data['pin_title'] if data['pin_title'] else 'Pin created by PinAutomatic'
	bookmark = int(data['bookmark']) if data['bookmark'] else None
	description = 'This Pin has been added auto-magically by the PinAutomatic app. Check it out on https://pinautomatic.herokuapp.com.'

	if data['description']:
		description = (data['description'][:498] + '..') if len(data['description'][0]) > 500 else data['description']

	print(source_url, requests_left, cont, bookmark, pin_link, pin_title, description)

	pa_token = session['pa-token']

	try:
		all_images = get_images(source_url, requests_left, cont, bookmark)

		if not all_images:
			response = {
				"data": "No Images to Pin. URL has no images? Or if Pinterest requests are exhausted, try again later? Or if all images on this page have been pinned, please try again with continue = False.",
				"code": 204
			}
			return jsonify(response)
	except Exception as e:
		response = {
			"data": f"Error while getting images from URL: {e}",
			"code": 422
		}
		return jsonify(response)

	try:
		job = q.enqueue_call(
			func=save_pins, args=(all_images, source_url, destination, bookmark, requests_left, cont, pa_token, current_user.id, pin_link, description, pin_title), result_ttl=1200, timeout=3600
		)
		session['job_id'] = job.get_id()
		# save_pins(all_images, source_url, destination, bookmark, requests_left, cont, pa_token, current_user.id, pin_link, description)
	except Exception as e:
		response = {
			"data": f"Error while adding job to RQ: {e}.",
			"code": 500
		}
		return jsonify(response)

	response = {
		"data": "Pin(s) will be added.",
		"code": 200
	}
	return jsonify(response)


@app.route('/get-requests-left')
@login_required
def get_requests_left():
	pinterest_req = get_pinterest_requests_left()
	pins_added = get_pins_added()

	res = {
		"pinterest_req_left": pinterest_req,
		"pins_added": pins_added,
		"code": 200
	}

	return jsonify(res)


@app.route('/check-last-pin-status', methods=['POST'])
@login_required
def check_last_pin_status():
	pins_available_from_subscription = get_pins_available_from_subscription(current_user.id)
	if pins_available_from_subscription == 0:
		res = {
			"code": 429,
			"data": "Pins exhausted. Please purchase more pins to continue using the app."
		}
		return res

	data = request.form.to_dict(flat=False)
	source = data['source'][0]
	destination_board = data['destination'][0]
	destination = get_board_id(destination_board)  # returns board ID

	last_pin_details = get_last_pin_details(source, destination)
	res = {
		"code": 404,
		"destination": destination
	}

	if last_pin_details:
		res = {
			"code": 200,
			"pins_copied": last_pin_details['pins_copied'],
			"destination": destination
		}

	return res


@app.route('/check-session-status')
@login_required
def check_session_status():
	session_status = dict()
	if "job_id" in session:
		job_key = session['job_id']
		try:
			job = Job.fetch(job_key, connection=conn)
		except Exception:
			session_status = {
				"status": "No pending Job.",
				"code": 404
			}
			return session_status

		if job.is_finished:
			session_status["status"] = f"Last Job completed: {job.result}"
			session_status["code"] = 200
		elif job.is_failed:
			session_status["status"] = f"""Last Job failed: {job.exc_info}

			If this error is unclear, please contact the developer about it.

			Otherwise, please enter new job."""
			session_status["code"] = 500
		elif not job.is_finished:
			session_status["status"] = "Not yet completed. Pinning..."
			session_status["code"] = 202
	else:
		session_status = {
			"status": "No pending Job.",
			"code": 404
		}

	return session_status


# # The Admin page requires an 'Admin' role.
# @app.route('/admin')
# @roles_required('Admin')    # Use of @roles_required decorator
# def admin_page():
#     pass


def save_pins(pins, source, destination, bookmark, req_left, cont, pa_token, current_user_id, pin_link, description, pin_title):
	counter = 0
	added = 0
	skipped = 0
	start_index = bookmark + 1 if cont is True else 0
	pins_available_from_subscription = get_pins_available_from_subscription(current_user_id)

	url = PINTEREST_API_BASE_URL + '/pins'

	headers = {
		"Authorization": f"Bearer {pa_token}",
		"Content-Type": "application/json",
	}

	for i in range(start_index, len(pins)):
		if pins_available_from_subscription == 0:
			return {"code": 429, "data": f"Pins exhausted. Please purchase more pins to continue using the app.\nAdded: {counter}\nSkipped: {skipped}"}

		put_data = {
			"board_id": destination,
			"description": description,
			"link": pin_link,
			"title": pin_title,
			"media_source": {
				"source_type": "image_url",
				"url": pins[i]
			}
		}

		try:
			r = requests.post(url, headers=headers, data=json.dumps(put_data))
			print(r.json())
		except requests.exceptions.RequestException as e:
			raise Exception(str({"code": 500, "data": str(e)}))

		if r.status_code == 201:
			counter += 1
			added += 1
			pins_available_from_subscription -= 1

			print(r.headers)

			time.sleep(10)

			if counter == 10:
				pinterest_requests_left = r.headers['x-userendpoint-ratelimit-remaining']
				update_stats(current_user_id=current_user_id, pinterest_requests_left=pinterest_requests_left, pins_added=10)
				update_pin_data(current_user_id, source, destination, cont, pins_added=10)
				counter = 0
		elif r.status_code == 429:
			raise Exception(str({"code": 429, "data": "Requests exhausted. Please try again later."}))
		elif r.status_code == 403:
			skipped += 1
		else:
			raise Exception(str({"code": 500, "data": f"{r.status_code}: {r.text}"}))

	del pins

	pinterest_requests_left = r.headers['x-userendpoint-ratelimit-remaining']
	update_stats(current_user_id=current_user_id, pinterest_requests_left=pinterest_requests_left, pins_added=counter)
	update_pin_data(current_user_id, source, destination, cont, pins_added=counter)

	res = {
		"pins_added": added,
		"pins_skipped": skipped
	}

	return {"code": 200, "data": res}


@app.route('/toggle-user-active/<user_id>')
def toggle_user_active(user_id):
	user_instance = User.query.filter_by(id=user_id).first()
	if user_instance.active:
		user_instance.active = False
		flag = "INACTIVE"
	else:
		user_instance.active = True
		flag = "ACTIVE"

	db.session.commit()
	return jsonify({"code": 200, "message": str(user_instance.email) + " has been marked active " + str(flag)})


def check_user_active():
	user_instance = User.query.filter_by(id=current_user.id).first()
	if user_instance.active:
		return True
	else:
		return False


@app.route('/purchase-pins')
@login_required
def purchase_pins():
	return render_template('purchase_pins.html')


@app.route('/payment_complete')
def payment_complete():
	stripe_session_id = request.args.get('session_id')
	checkout_session = stripe.checkout.Session.retrieve(stripe_session_id)

	if checkout_session['payment_status'] == 'paid':
		pay_amount = int(checkout_session['amount_total'])/100

		pay_to_pin_map = {
			10: 1000,
			40: 5000,
			70: 10000,
		}
		pins_bought = pay_to_pin_map[pay_amount]

		update_payment(stripe_session_id, pay_amount, pins_bought)

		return render_template('payment_complete.html', data={'payment_success': True})
	elif checkout_session['payment_status'] == 'unpaid':
		return render_template('payment_complete.html', data={'payment_success': False})

	print(checkout_session)


@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
	pin_bundles = {
		1: {'price': 1000},
		2: {'price': 4000},
		3: {'price': 7000},
	}

	data = request.json
	bundle_id = int(data['bundle_id'])

	try:
		checkout_session = stripe.checkout.Session.create(
			payment_method_types=['card'],
			line_items=[
				{
					'price_data': {
						'currency': 'usd',
						'unit_amount': pin_bundles[bundle_id]['price'],
						'product_data': {
							'name': 'PinAutomatic Pin Bundle',
							'images': ['https://i.imgur.com/EHyR2nP.png'],
						},
					},
					'quantity': 1,
				},
			],
			mode='payment',
			success_url= SITE_SCHEME + "://" + SITE_DOMAIN + "/payment_complete?session_id={CHECKOUT_SESSION_ID}",
			cancel_url= SITE_SCHEME + "://" + SITE_DOMAIN + "/payment_complete?session_id={CHECKOUT_SESSION_ID}",
		)
		print(checkout_session)
		save_stripe_session_id(checkout_session.id)
		return jsonify({'id': checkout_session.id})
	except Exception as e:
		print('HERE', str(e))
		return jsonify(error=str(e)), 403
