#!/bin/sh
set -e
flask --app 'app:create_app' db upgrade
flask --app 'app:create_app' seed
exec gunicorn -w 3 -b 0.0.0.0:${PORT:-5000} 'app:create_app()'
