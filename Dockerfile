FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app:create_app

EXPOSE ${PORT:-5000}

CMD gunicorn -w 3 -b 0.0.0.0:${PORT:-5000} 'app:create_app()'
