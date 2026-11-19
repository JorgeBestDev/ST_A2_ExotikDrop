from datetime import datetime, timezone

from sqlalchemy import Index, text

from app.extensions import db


class InventoryReservation(db.Model):
    __tablename__ = 'inventory_reservations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, unique=True)
    idempotency_key = db.Column(db.String(64), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', back_populates='inventory_reservations')
    order = db.relationship('Order', back_populates='inventory_reservation')
    items = db.relationship(
        'InventoryReservationItem',
        back_populates='reservation',
        cascade='all, delete-orphan',
    )

    __table_args__ = (
        db.UniqueConstraint('user_id', 'idempotency_key', name='uq_inventory_reservation_user_key'),
        db.CheckConstraint(
            "status IN ('active', 'consumed', 'expired', 'released')",
            name='ck_inventory_reservation_status',
        ),
        db.Index(
            'uq_inventory_reservation_active_user',
            'user_id',
            unique=True,
            postgresql_where=text("status = 'active'"),
            sqlite_where=text("status = 'active'"),
        ),
        db.Index('ix_inventory_reservation_expiry', 'status', 'expires_at'),
    )

    def __repr__(self):
        return f'<InventoryReservation {self.id} for order {self.order_id}>'


class InventoryReservationItem(db.Model):
    __tablename__ = 'inventory_reservation_items'

    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('inventory_reservations.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    reservation = db.relationship('InventoryReservation', back_populates='items')
    product = db.relationship('Product')

    __table_args__ = (
        db.UniqueConstraint('reservation_id', 'product_id', name='uq_reservation_product'),
        db.CheckConstraint('quantity > 0', name='ck_reservation_item_quantity_positive'),
    )

    def __repr__(self):
        return f'<InventoryReservationItem {self.product_id} x {self.quantity}>'
