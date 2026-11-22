import os
from decimal import Decimal
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(test_config=None):
    app = Flask(__name__)

    database_url = os.getenv("DATABASE_URL", "sqlite:///amar_dokan.db")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "development-only-change-me"),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        CURRENCY="৳",
    )
    if test_config: app.config.update(test_config)
    db.init_app(app); migrate.init_app(app, db); csrf.init_app(app)
    login_manager.init_app(app); login_manager.login_view = "main.login"
    @app.template_filter("taka")
    def taka(value): return f"{Decimal(value):,.2f} টাকা"
    from .models import User
    @login_manager.user_loader
    def load_user(user_id): return db.session.get(User, int(user_id))
    from .routes import bp
    app.register_blueprint(bp)
    from .cli import seed
    app.cli.add_command(seed)
    return app
