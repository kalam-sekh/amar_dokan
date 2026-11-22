# আমার দোকান (Amar Dokan)

A Bengali-first, mobile-friendly grocery store built with Flask, PostgreSQL and progressive enhancement. Prices use `Decimal`/PostgreSQL `NUMERIC`, never floats.

## Start locally

1. Copy `.env.example` to `.env` and change the secret plus admin password.
2. Start the stack: `docker compose up --build -d`.
3. Create schema and sample inventory: `docker compose exec web flask --app 'app:create_app' db upgrade` then `docker compose exec web flask --app 'app:create_app' seed`.
4. Open `http://localhost:5000`. Admin login uses the credentials in `.env`.

Without Docker, create a virtual environment, install `requirements.txt`, set `DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost/amar_dokan`, then run the same Flask migration/seed commands and `flask --app 'app:create_app' run`.

## Images

The seeded catalog deliberately uses generated `placehold.co` fallback artwork: it has no third-party copyright ambiguity. To import images you have verified on Wikimedia Commons/Openverse as CC-licensed, make a metadata file from `scripts/images.example.json` and run `python scripts/import_images.py images.json`. The importer rejects non-image responses and images over 8 MB, strips unsafe filenames, and writes `ATTRIBUTION.md`; do not remove this credit file. For production, store originals in object storage and serve resized WebP through a CDN.

## Reliability and scaling

Checkout locks each product row with PostgreSQL `FOR UPDATE`, verifies stock, and decrements it within the same transaction. Run multiple Gunicorn workers behind a reverse proxy; use managed PostgreSQL with backups/read replicas, Redis for server-side sessions/rate limits, object storage/CDN for images, background workers for notifications, and add payment-provider idempotency keys before accepting payment. Keep HTTPS, a strong `SECRET_KEY`, secure cookies, CSRF enabled, password policies, rate limiting, audit logs, and database migrations in production.

## Tests

Run `pytest`. The included smoke test covers Bengali catalog rendering and decimal cart pricing.
