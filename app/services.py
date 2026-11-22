from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import select
from . import db
from .models import Order, OrderLine, Product

MONEY = Decimal("0.01")
def money(value): return Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP)

def create_order(user, cart):
    """Atomically reserve stock. PostgreSQL row locks prevent overselling."""
    if not cart: raise ValueError("ব্যাগ খালি")
    order = Order(user=user, total=Decimal("0")); total = Decimal("0")
    for raw_id, raw_qty in cart.items():
        product = db.session.execute(select(Product).where(Product.id == int(raw_id), Product.active.is_(True)).with_for_update()).scalar_one_or_none()
        qty = Decimal(str(raw_qty))
        if not product or qty <= 0: raise ValueError("পণ্য পাওয়া যায়নি")
        if product.stock_base < qty: raise ValueError(f"{product.name_bn} পর্যাপ্ত নেই")
        line_total = money(product.price_per_base * qty)
        product.stock_base -= qty
        order.lines.append(OrderLine(product_id=product.id, product_name_bn=product.name_bn, quantity_base=qty,
          unit_label=product.base_unit, unit_price=product.price_per_base, line_total=line_total))
        total += line_total
    order.total = money(total); db.session.add(order); db.session.commit()
    return order
