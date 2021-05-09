import math
import os
import urllib.parse
from datetime import datetime

import requests
from flask import abort, request, session
from flask_user import UserManager, current_user
from bs4 import BeautifulSoup

from app import app, db
from models import IPDetails, PinData, PinterestData, Stats, Token, User

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


def save_profile_and_return_requests_left():
	headers = {
		"Authorization": f"Bearer {session['pa-token']}"
	}

	url = PINTEREST_API_BASE_URL + '/users/me'
	r = requests.get(url, headers=headers)
	if r.status_code == 200:
		res = r.json()

		print(res)

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

		return {"data": r.headers['x-userendpoint-ratelimit-remaining'], "code": 200}
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
			"pins_copied": pin_data.bookmark
		}

	return data


def update_pin_data(source, destination, bookmark, current_user_id):
	if not PinData.query.filter_by(user_id=current_user_id, source_board=source, destination_board=destination).first():
		pin_data = PinData(
			user_id=current_user_id,
			source_board=source,
			destination_board=destination,
			bookmark=bookmark,
		)
		db.session.add(pin_data)
	else:
		pin_data_instance = PinData.query.filter_by(user_id=current_user_id, source_board=source, destination_board=destination).first()
		pin_data_instance.pins_copied += pins_added
		pin_data_instance.bookmark = bookmark

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


def create_board_if_not_exists(board_name):
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

# def get_next_pins(source, req_left, cont, cursor):
# 	remainder = math.ceil(int(req_left)/250)  #250 is max page_size with v3

# 	print("Remainder = " + str(remainder))

# 	all_pins = []

# 	params = {
# 		"page_size": 250,
# 		"filter_section_pins": False,
# 		"filter_stories": True
# 	}
# 	if cont == "true":
# 		params["bookmark"] = cursor

# 	headers = {
# 		"Authorization": f"Bearer {session['pa-token']}"
# 	}

# 	for x in range(remainder):
# 		session['status'] = "Fetching Pins: " + str((x + 1) * 250)
# 		url_params = urllib.parse.urlencode(params)
# 		url = PINTEREST_API_BASE_URL + f"/boards/{source}/pins"
# 		r = requests.get(url, params=url_params, headers=headers)

# 		print(url)

# 		print(r.json())

# 		abort(500)

# 		if r.status_code == 200:
# 			res = r.json()
# 			all_pins = all_pins + res["data"]

# 			if res["page"]["cursor"] != None:
# 				params["cursor"] = res["page"]["cursor"]
# 			else:
# 				# If requests left > number of pins in the source board
# 				params["cursor"] = ""
# 				break
# 		else:
# 			print(r.json())
# 			abort(500)

# 	response = {
# 		"all_pins": all_pins,
# 		"last_cursor": params["cursor"]
# 	}

# 	return response


def get_images(url, req_left, cont, bookmark):
	r = requests.get(url, timeout=10)
	htmldata = r.text
	images = {}
	x = 0

	soup = BeautifulSoup(htmldata, 'html.parser')
	all_images = soup.find_all('img')
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
		images[x] = all_images[x]

	print(images)

	return images if images != {} else None