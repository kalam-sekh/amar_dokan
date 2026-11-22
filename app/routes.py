from decimal import Decimal
from functools import wraps
from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import select
from . import db
from .models import Category, Order, Product, User
from .services import create_order

bp = Blueprint("main", __name__)
def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin: abort(403)
        return view(*args, **kwargs)
    return wrapped
def cart(): return session.setdefault("cart", {})
@bp.get("/")
def index():
    return render_template("index.html", products=db.session.scalars(select(Product).where(Product.active.is_(True))).all(), categories=db.session.scalars(select(Category)).all())
@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = db.session.scalar(select(User).where(User.email == request.form["email"].lower()))
        if user and user.check_password(request.form["password"]): login_user(user); return redirect(url_for("main.index"))
        flash("ইমেইল বা পাসওয়ার্ড ঠিক নয়")
    return render_template("auth.html", mode="login")
@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if db.session.scalar(select(User).where(User.email == request.form["email"].lower())): flash("এই ইমেইল আগে ব্যবহার হয়েছে")
        else:
            user=User(name=request.form["name"], email=request.form["email"].lower()); user.set_password(request.form["password"]); db.session.add(user); db.session.commit(); login_user(user); return redirect(url_for("main.index"))
    return render_template("auth.html", mode="register")
@bp.post("/bag")
def update_bag():
    data=request.get_json(); product=db.session.get(Product, int(data["product_id"])); qty=Decimal(str(data["quantity_base"]))
    if not product or qty <= 0: return jsonify(error="ভুল পণ্য"), 400
    c=cart(); c[str(product.id)] = str(Decimal(c.get(str(product.id), "0")) + qty); session.modified=True
    return bag_summary()
@bp.get("/bag/summary")
def bag_summary():
    c=cart(); ids=[int(x) for x in c] or [-1]; products=db.session.scalars(select(Product).where(Product.id.in_(ids))).all()
    total=sum((p.price_per_base * Decimal(c[str(p.id)]) for p in products), Decimal("0"))
    return jsonify(count=len(c), total=f"{total:.2f}")
@bp.get("/checkout")
@login_required
def checkout():
    c=cart(); ids=[int(x) for x in c] or [-1]; products=db.session.scalars(select(Product).where(Product.id.in_(ids))).all()
    lines=[(p, Decimal(c[str(p.id)]), p.price_per_base * Decimal(c[str(p.id)])) for p in products]
    return render_template("checkout.html", lines=lines, total=sum((x[2] for x in lines), Decimal("0")))
@bp.post("/checkout")
@login_required
def place_order():
    try: order=create_order(current_user, cart()); session["cart"]={}; session.modified=True; flash("অর্ডার নেওয়া হয়েছে। ধন্যবাদ!"); return redirect(url_for("main.orders"))
    except ValueError as exc: db.session.rollback(); flash(str(exc)); return redirect(url_for("main.checkout"))
@bp.get("/orders")
@login_required
def orders(): return render_template("orders.html", orders=db.session.scalars(select(Order).where(Order.user_id==current_user.id).order_by(Order.created_at.desc())).all())
@bp.get("/admin")
@admin_required
def admin(): return render_template("admin.html", products=db.session.scalars(select(Product).order_by(Product.name_bn)).all(), orders=db.session.scalars(select(Order).order_by(Order.created_at.desc()).limit(20)).all())
@bp.post("/admin/product/<int:product_id>")
@admin_required
def update_product(product_id):
    p=db.session.get(Product, product_id); p.price_per_base=Decimal(request.form["price"]); p.stock_base=Decimal(request.form["stock"]); p.active="active" in request.form; db.session.commit(); flash("পণ্য হালনাগাদ হয়েছে"); return redirect(url_for("main.admin"))
@bp.get("/logout")
def logout(): logout_user(); return redirect(url_for("main.index"))
