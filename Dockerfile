FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app:create_app

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE ${PORT:-5000}

CMD ["./entrypoint.sh"]
