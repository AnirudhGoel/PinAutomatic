import os
import datetime
from flask import Flask, render_template, session, request, redirect, url_for, flash
from flask_babelex import Babel

from flask_sqlalchemy import SQLAlchemy
from flask_user import current_user, login_required, roles_required, UserManager, UserMixin
from .config import ConfigClass


app = Flask(__name__)
app.config.from_object(ConfigClass)

PINTEREST_CLIENT_ID = os.environ.get("PINTEREST_CLIENT_ID")


db = SQLAlchemy(app)
from .models import User, Role
babel = Babel(app)

# Setup Flask-User and specify the User data-model
user_manager = UserManager(app, db, User)

# Create all database tables
db.create_all()


# Create 'admin@example.com' user with 'Admin' role
if not User.query.filter(User.email == 'admin@example.com').first():
    user = User(
        email='admin@example.com',
        email_confirmed_at=datetime.datetime.utcnow(),
        password=user_manager.hash_password('yankring'),
    )
    user.roles.append(Role(name='Admin'))
    db.session.add(user)
    db.session.commit()




@app.route('/')
@login_required
def index():
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
            return redirect(url_for('get_and_save_token'), temp_code=temp_code)
        else:
            flash("You need to provide authorization to PinterestAutomatic to allow adding of pins to your board.", category='error')
            return redirect(url_for('index'))
    else:
        return redirect(url_for('logout_user'))



@login_required
def get_and_save_token(temp_code):
    print(temp_code)
    pass


# The Admin page requires an 'Admin' role.
@app.route('/admin')
@roles_required('Admin')    # Use of @roles_required decorator
def admin_page():
    pass