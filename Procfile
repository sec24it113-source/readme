web: gunicorn run:app --bind 0.0.0.0:$PORT
worker: celery -A run.celery worker --loglevel=info
beat: celery -A run.celery beat --loglevel=info
