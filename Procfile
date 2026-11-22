web: gunicorn -w 3 -b 0.0.0.0:$PORT 'app:create_app()'
release: flask --app 'app:create_app' db upgrade
