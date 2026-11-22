import os
from decimal import Decimal
from functools import wraps
from pathlib import Path
from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func, select
from werkzeug.utils import secure_filename
from . import db
from .models import Category, Order, Product, User
from .services import create_order

bp = Blueprint("main", __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
UPLOAD_FOLDER = Path(__file__).parent / 'static' / 'images'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin: abort(403)
        return view(*args, **kwargs)
    return wrapped

def cart(): return session.setdefault("cart", {})

def admin_context():
    product_count = db.session.scalar(select(func.count(Product.id)))
    pending_orders = db.session.scalar(select(func.count(Order.id)).where(Order.status == 'নতুন'))
    return dict(product_count=product_count, pending_orders=pending_orders)

# ── Storefront ──

@bp.get("/")
def index():
    return render_template("index.html", products=db.session.scalars(select(Product).where(Product.active.is_(True))).all(), categories=db.session.scalars(select(Category)).all())

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = db.session.scalar(select(User).where(User.email == request.form["email"].lower()))
        if user and user.check_password(request.form["password"]): login_user(user); return redirect(url_for("main.index"))
        flash("ইমেইল বা পাসওয়ার্ড ঠিক নয়")
    return render_template("auth.html", mode="login")

@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if db.session.scalar(select(User).where(User.email == request.form["email"].lower())): flash("এই ইমেইল আগে ব্যবহার হয়েছে")
        else:
            user=User(name=request.form["name"], email=request.form["email"].lower()); user.set_password(request.form["password"]); db.session.add(user); db.session.commit(); login_user(user); return redirect(url_for("main.index"))
    return render_template("auth.html", mode="register")

@bp.post("/bag")
def update_bag():
    data=request.get_json(); product=db.session.get(Product, int(data["product_id"])); qty=Decimal(str(data["quantity_base"]))
    if not product or qty <= 0: return jsonify(error="ভুল পণ্য"), 400
    c=cart(); c[str(product.id)] = str(Decimal(c.get(str(product.id), "0")) + qty); session.modified=True
    summary = bag_summary().get_json()
    summary["product_qty"] = str(c[str(product.id)])
    summary["base_unit"] = product.base_unit
    return jsonify(summary)

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
    try: order=create_order(current_user, cart()); session["cart"]={}; session.modified=True; flash("অর্ডার নেওয়া হয়েছে। ধন্যবাদ!"); return redirect(url_for("main.orders"))
    except ValueError as exc: db.session.rollback(); flash(str(exc)); return redirect(url_for("main.checkout"))

@bp.get("/orders")
@login_required
def orders(): return render_template("orders.html", orders=db.session.scalars(select(Order).where(Order.user_id==current_user.id).order_by(Order.created_at.desc())).all())

@bp.get("/logout")
def logout(): logout_user(); return redirect(url_for("main.index"))

# ── Admin ──

@bp.get("/admin")
@admin_required
def admin():
    total_revenue = db.session.scalar(select(func.coalesce(func.sum(Order.total), 0))) or 0
    total_orders = db.session.scalar(select(func.count(Order.id)))
    pending_count = db.session.scalar(select(func.count(Order.id)).where(Order.status == 'নতুন'))
    total_products = db.session.scalar(select(func.count(Product.id)))
    active_products = db.session.scalar(select(func.count(Product.id)).where(Product.active.is_(True)))
    total_customers = db.session.scalar(select(func.count(User.id)).where(User.is_admin.is_(False)))
    recent_orders = db.session.scalars(select(Order).order_by(Order.created_at.desc()).limit(10)).all()
    low_stock = db.session.scalars(select(Product).where(Product.stock_base < 1000, Product.active.is_(True)).order_by(Product.stock_base)).all()
    return render_template("admin.html", page="dashboard",
        total_revenue=total_revenue, total_orders=total_orders, pending_count=pending_count,
        total_products=total_products, active_products=active_products, total_customers=total_customers,
        recent_orders=recent_orders, low_stock=low_stock, **admin_context())

@bp.get("/admin/products")
@admin_required
def admin_products():
    products = db.session.scalars(select(Product).order_by(Product.name_bn)).all()
    categories = db.session.scalars(select(Category).order_by(Category.name_bn)).all()
    return render_template("admin_products.html", page="products", products=products, categories=categories, **admin_context())

@bp.post("/admin/product/add")
@admin_required
def admin_add_product():
    image_url = "/static/images/placeholder.jpg"
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
            file.save(UPLOAD_FOLDER / filename)
            image_url = f"/static/images/{filename}"
    product = Product(
        name_bn=request.form["name_bn"],
        description_bn=request.form.get("description_bn") or None,
        category_id=int(request.form["category_id"]),
        base_unit=request.form["base_unit"],
        price_per_base=Decimal(request.form["price_per_base"]),
        stock_base=Decimal(request.form["stock_base"]),
        active="active" in request.form,
        image_url=image_url,
    )
    db.session.add(product)
    db.session.commit()
    flash("Product added successfully")
    return redirect(url_for("main.admin_products"))

@bp.post("/admin/product/<int:product_id>")
@admin_required
def update_product(product_id):
    p = db.session.get(Product, product_id)
    if not p: abort(404)
    p.name_bn = request.form.get("name_bn", p.name_bn)
    p.description_bn = request.form.get("description_bn") or None
    if "category_id" in request.form:
        p.category_id = int(request.form["category_id"])
    if "base_unit" in request.form:
        p.base_unit = request.form["base_unit"]
    p.price_per_base = Decimal(request.form["price"])
    p.stock_base = Decimal(request.form["stock"])
    p.active = "active" in request.form
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
            file.save(UPLOAD_FOLDER / filename)
            p.image_url = f"/static/images/{filename}"
    db.session.commit()
    flash("Product updated successfully")
    return redirect(url_for("main.admin_products"))

@bp.post("/admin/product/<int:product_id>/delete")
@admin_required
def delete_product(product_id):
    p = db.session.get(Product, product_id)
    if p:
        db.session.delete(p)
        db.session.commit()
        flash("Product deleted")
    return redirect(url_for("main.admin_products"))

@bp.get("/admin/orders")
@admin_required
def admin_orders():
    orders = db.session.scalars(select(Order).order_by(Order.created_at.desc())).all()
    return render_template("admin_orders.html", page="orders", orders=orders, **admin_context())

@bp.post("/admin/order/<int:order_id>/status")
@admin_required
def update_order_status(order_id):
    order = db.session.get(Order, order_id)
    if order:
        order.status = request.form["status"]
        db.session.commit()
        flash(f"Order #{order.id} status updated")
    return redirect(url_for("main.admin_orders"))

@bp.get("/admin/categories")
@admin_required
def admin_categories():
    categories = db.session.scalars(select(Category).order_by(Category.name_bn)).all()
    return render_template("admin_categories.html", page="categories", categories=categories, **admin_context())

@bp.post("/admin/category/add")
@admin_required
def admin_add_category():
    cat = Category(name_bn=request.form["name_bn"])
    db.session.add(cat)
    db.session.commit()
    flash("Category added")
    return redirect(url_for("main.admin_categories"))

@bp.post("/admin/category/<int:cat_id>/delete")
@admin_required
def admin_delete_category(cat_id):
    cat = db.session.get(Category, cat_id)
    if cat:
        if cat.products:
            flash("Cannot delete category with products")
        else:
            db.session.delete(cat)
            db.session.commit()
            flash("Category deleted")
    return redirect(url_for("main.admin_categories"))

@bp.get("/admin/customers")
@admin_required
def admin_customers():
    users = db.session.scalars(select(User).order_by(User.created_at.desc())).all()
    return render_template("admin_customers.html", page="customers", users=users, **admin_context())
