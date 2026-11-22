import click
from flask import current_app
from flask.cli import with_appcontext
from sqlalchemy import select
from . import db
from .models import Category, Product, User

@click.command("seed")
@with_appcontext
def seed():
    if db.session.query(Product).first():
        click.echo("Catalog already exists")
        ensure_admin()
        return
    staples=Category(name_bn="নিত্যপণ্য"); produce=Category(name_bn="সবজি ও ফল"); db.session.add_all([staples,produce]); db.session.flush()
    items=[("চাল",staples,"g",0.075,50000,"rice.jpg"), ("মসুর ডাল",staples,"g",0.16,20000,"lentils.jpg"), ("সয়াবিন তেল",staples,"ml",0.19,30000,"soybean_oil.jpg"), ("ডিম",staples,"piece",12,500,"eggs.jpg"), ("আলু",produce,"g",0.04,30000,"potatoes.jpg"), ("পেঁয়াজ",produce,"g",0.07,20000,"onions.jpg"), ("কলা",produce,"piece",8,300,"bananas.jpg")]
    for name,cat,unit,price,stock,img in items: db.session.add(Product(name_bn=name,category=cat,base_unit=unit,price_per_base=price,stock_base=stock,image_url=f"/static/images/{img}"))
    ensure_admin()
    db.session.commit(); click.echo("Sample catalog and admin created")

def ensure_admin():
    email = current_app.config.get("ADMIN_EMAIL", "admin@example.com")
    password = current_app.config.get("ADMIN_PASSWORD", "ChangeMeImmediately123!")
    user = db.session.scalar(select(User).where(User.email == email))
    if user:
        user.is_admin = True
        user.set_password(password)
        db.session.commit()
        click.echo(f"Admin updated: {email}")
    else:
        admin = User(name="প্রশাসক", email=email, is_admin=True)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Admin created: {email}")
