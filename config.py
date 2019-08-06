import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

environ = os.environ

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = environ.get('SECRET_KEY')

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False    # Avoids SQLAlchemy warning

    # Flask-Mail SMTP server settings
    MAIL_SERVER = environ.get('MAIL_SERVER')
    MAIL_PORT = environ.get('MAIL_PORT')
    MAIL_USE_SSL = environ.get('MAIL_USE_SSL')
    MAIL_USE_TLS = environ.get('MAIL_USE_TLS')
    MAIL_USERNAME = environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = environ.get('MAIL_DEFAULT_SENDER')

    # Flask-User settings
    USER_APP_NAME = environ.get('USER_APP_NAME')      # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = environ.get('USER_ENABLE_EMAIL')
    USER_ENABLE_USERNAME = environ.get('USER_ENABLE_USERNAME')
    USER_EMAIL_SENDER_NAME = USER_APP_NAME
    USER_EMAIL_SENDER_EMAIL = environ.get('USER_EMAIL_SENDER_EMAIL')

    print(environ.get('USER_ENABLE_USERNAME'))
    print(USER_ENABLE_USERNAME)


