import os
from flask import Flask, render_template, session, request, redirect, url_for, flash
from flask_babelex import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_user import current_user, login_required
from config import ConfigClass


app = Flask(__name__)
app.config.from_object(ConfigClass)


db = SQLAlchemy(app)
babel = Babel(app)
from services import get_token, save_token_to_database

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


# # The Admin page requires an 'Admin' role.
# @app.route('/admin')
# @roles_required('Admin')    # Use of @roles_required decorator
# def admin_page():
#     pass
