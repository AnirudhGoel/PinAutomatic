web: gunicorn app:app
release: python manage.py db upgrade
worker: python worker.py