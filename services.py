import math
import os
import urllib.parse as urlparse
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from flask import abort, request, session
from flask_user import UserManager, current_user

from .app import app, db
from .models import (IPDetails, Payments, PinData, PinterestData, Stats, Token,
                    User)

# Setup Flask-User and specify the User data-model
user_manager = UserManager(app, db, User)

PINTEREST_CLIENT_ID = os.environ.get("PINTEREST_CLIENT_ID")
PINTEREST_API_BASE_URL = os.environ.get("PINTEREST_API_BASE_URL")
PINTEREST_CLIENT_SECRET = os.environ.get("PINTEREST_CLIENT_SECRET")


def get_token(temp_code, redirect_uri):
	data = {
		"grant_type": "authorization_code",
		"client_id": PINTEREST_CLIENT_ID,
		"client_secret": PINTEREST_CLIENT_SECRET,
		"code": temp_code,
		"redirect_uri": redirect_uri
	}

	# url_params = urllib.parse.urlencode(params)
	token_url = PINTEREST_API_BASE_URL + "/oauth/access_token"
	r = requests.post(token_url, data=data)
	response = r.json()
	print(response)
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


def update_pinterest_profile():
	headers = {
		"Authorization": f"Bearer {session['pa-token']}"
	}

	url = PINTEREST_API_BASE_URL + '/users/me'
	r = requests.get(url, headers=headers)
	if r.status_code == 200:
		res = r.json()
		res = res["data"]

		if not PinterestData.query.filter_by(user_id=current_user.id).first():
			pinterest_data = PinterestData(
				user_id=current_user.id,
				pinterest_id=res["id"],
				username=res["username"],
				full_name=res["full_name"],
				pins=res["pin_count"],
				boards=res["board_count"],
				followers=res["follower_count"],
				following=res["following_count"],
			)
			db.session.add(pinterest_data)
		else:
			pinterest_data_instance = PinterestData.query.filter_by(user_id=current_user.id).first()
			pinterest_data_instance.username = res["username"]
			pinterest_data_instance.full_name = res["full_name"]
			pinterest_data_instance.pins = res["pin_count"]
			pinterest_data_instance.boards = res["board_count"]
			pinterest_data_instance.followers = res["follower_count"]
			pinterest_data_instance.following = res["following_count"]

		db.session.commit()

		return {"full_name": res['full_name'], "code": 200}
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

	print(source, destination, pin_data)

	data = None

	if pin_data:
		data = {
			"pins_copied": pin_data.bookmark
		}

	return data


def update_pin_data(current_user_id, source, destination, cont, pins_added):
	if cont:  # if cont, then we update the existing bookmark
		pin_data_instance = PinData.query.filter_by(user_id=current_user_id, source_board=source, destination_board=destination).first()
		pin_data_instance.bookmark += pins_added
	else:  # if not cont, then either there was no entry in PinData or we overwrite existing entry
		if not PinData.query.filter_by(user_id=current_user_id, source_board=source, destination_board=destination).first():
			pin_data = PinData(
				user_id=current_user_id,
				source_board=source,
				destination_board=destination,
				bookmark=pins_added,
			)
			db.session.add(pin_data)
		else:
			pin_data_instance = PinData.query.filter_by(user_id=current_user_id, source_board=source, destination_board=destination).first()
			pin_data_instance.bookmark = pins_added

	db.session.commit()
	return True


def update_stats(current_user_id, pinterest_requests_left=None, pins_added=None):
	# If Stats does not exist, it will be created on the first call to Home URL
	if not Stats.query.filter_by(user_id=current_user_id).first():
		pinterest_requests_left = pinterest_requests_left if pinterest_requests_left else 0
		stats_data = Stats(
			user_id=current_user_id,
			pinterest_requests_left=pinterest_requests_left
		)
		db.session.add(stats_data)
	else:
		stats_instance = Stats.query.filter_by(user_id=current_user_id).first()
		stats_instance.pins_added = stats_instance.pins_added + pins_added if pins_added else stats_instance.pins_added
		stats_instance.pinterest_requests_left = pinterest_requests_left if pinterest_requests_left else stats_instance.pinterest_requests_left
		stats_instance.last_pin_at = datetime.utcnow()

	db.session.commit()
	return True


def update_pinterest_requests_left():
	headers = {
		"Authorization": f"Bearer {session['pa-token']}"
	}

	url = PINTEREST_API_BASE_URL + '/pins'
	r = requests.put(url, headers=headers)
	if r.status_code == 400:  # 400 Bad Request expected as we are not passing Board ID
		update_stats(current_user.id, pinterest_requests_left=r.headers['x-userendpoint-ratelimit-remaining'])
	elif r.status_code == 429:
		update_stats(current_user.id, pinterest_requests_left=0)


def get_pinterest_requests_left():
	stats_instance = Stats.query.filter_by(user_id=current_user.id).first()
	return int(stats_instance.pinterest_requests_left)


def get_board_id(board_name):
	headers = {
		"Authorization": f"Bearer {session['pa-token']}"
	}

	data = {
		"name": board_name,
		"return_existing": True
	}

	url = PINTEREST_API_BASE_URL + '/boards'
	r = requests.put(url, data=data, headers=headers)
	if r.status_code == 200:
		res = r.json()
		board_id = res['data']['id']

	return board_id


def get_pins_available_from_subscription(current_user_id):
	payments_data = Payments.query.filter_by(user_id=current_user_id).first()
	total_pins_purchased = int(payments_data.pins_bought)

	stats_data = Stats.query.filter_by(user_id=current_user_id).first()
	pins_added = int(stats_data.pins_added)

	return total_pins_purchased - pins_added if total_pins_purchased > pins_added else 0


def get_pins_added():
	pins_added = 0

	if not Stats.query.filter_by(user_id=current_user.id).first():
		stats = Stats(
			user_id=current_user.id
		)
		db.session.add(stats)
		db.session.commit()
	else:
		stats = Stats.query.filter_by(user_id=current_user.id).first()
		pins_added = stats.pins_added

	return pins_added


def get_total_pins_from_subscription():
	total_pins_from_subscription = 0

	if not Payments.query.filter_by(user_id=current_user.id).first():
		payments = Payments(
			user_id=current_user.id
		)
		db.session.add(payments)
		db.session.commit()
	else:
		payments_instance = Payments.query.filter_by(user_id=current_user.id).first()
		total_pins_from_subscription = payments_instance.pins_bought

	return total_pins_from_subscription


def get_images(url, req_left, cont, bookmark):
	r = requests.get(url, timeout=10)
	htmldata = r.text
	all_images = []
	images = {}
	x = 0

	soup = BeautifulSoup(htmldata, 'html.parser')
	all_image_elements = soup.find_all('img')

	for image_element in all_image_elements:
		all_images.append(image_element['src'])

	max_images = len(all_images)

	if cont:
		if len(all_images) > bookmark:  # Do we have more images after bookmark
			if len(all_images) - bookmark > req_left:
				max_images = bookmark + req_left
		else:  # If not, then we return None
			return None
	else:
		if len(all_images) > req_left:
			max_images = req_left

	for x in range(max_images):  # If there are no images on the page, this will keep images = {}
		images[x] = urlparse.urljoin(url, all_images[x])

	print(images)

	return images if images != {} else None


def save_stripe_session_id(session_id):
	payments_instance = Payments.query.filter_by(user_id=current_user.id).first()
	payments_instance.stripe_session_id = session_id

	db.session.commit()


def update_payment(stripe_session_id, amount, pins_bought, currency='USD'):
	payments_instance = Payments.query.filter_by(stripe_session_id=stripe_session_id).first()
	payments_instance.amount_received += amount
	payments_instance.pins_bought += pins_bought
	payments_instance.stripe_session_id = ''

	db.session.commit()