import os
from flask import Flask, render_template, session, request
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
PINTEREST_CLIENT_ID = os.getenv("PINTEREST_CLIENT_ID")

app = Flask(__name__)


@app.route('/')
def index():

    client_id = PINTEREST_CLIENT_ID

    if 'pa-token' in session:
        return render_template('index.html', title='Home')
    else:
        return render_template('login.html', title='Login')


@app.route('/login', methods=['POST'])
def login():
    pass
    # session['username'] = request.form['username']
    # return redirect(url_for('index'))
