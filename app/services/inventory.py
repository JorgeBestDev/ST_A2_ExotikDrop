from datetime import datetime, timezone

from sqlalchemy import func, select

from app.extensions import db
from app.models.inventory_reservations import InventoryReservation, InventoryReservationItem


def utc_now():
    return datetime.now(timezone.utc)


def as_utc(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def reserved_quantities(product_ids, now=None):
    product_ids = tuple(sorted(set(product_ids)))
    if not product_ids:
        return {}

    now = now or utc_now()
    rows = db.session.execute(
        select(
            InventoryReservationItem.product_id,
            func.sum(InventoryReservationItem.quantity),
        )
        .join(InventoryReservation, InventoryReservation.id == InventoryReservationItem.reservation_id)
        .where(
            InventoryReservationItem.product_id.in_(product_ids),
            InventoryReservation.status == 'active',
            InventoryReservation.expires_at > now,
        )
        .group_by(InventoryReservationItem.product_id)
    ).all()
    return {product_id: int(quantity) for product_id, quantity in rows}


def available_stock(product, now=None, reserved=None):
    if reserved is None:
        reserved = reserved_quantities([product.id], now).get(product.id, 0)
    return product.stock - reserved


def expire_reservations(user_id=None, now=None):
    now = now or utc_now()
    query = InventoryReservation.query.filter(
        InventoryReservation.status == 'active',
        InventoryReservation.expires_at <= now,
    )
    if user_id is not None:
        query = query.filter(InventoryReservation.user_id == user_id)

    reservations = query.order_by(InventoryReservation.id.asc()).with_for_update().all()
    for reservation in reservations:
        reservation.status = 'expired'
        if reservation.order.status == 'pending':
            reservation.order.status = 'expired'
        if reservation.order.payment and reservation.order.payment.status == 'pending':
            reservation.order.payment.status = 'expired'
    return reservations
