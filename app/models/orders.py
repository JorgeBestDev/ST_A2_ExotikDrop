from datetime import datetime, timezone

from app.extensions import db


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    shipping_recipient = db.Column(db.String(255), nullable=False, default='')
    shipping_phone = db.Column(db.String(40), nullable=False, default='')
    shipping_line1 = db.Column(db.String(255), nullable=False, default='')
    shipping_line2 = db.Column(db.String(255), nullable=True)
    shipping_city = db.Column(db.String(120), nullable=False, default='')
    shipping_region = db.Column(db.String(120), nullable=False, default='')
    shipping_postal_code = db.Column(db.String(30), nullable=False, default='')
    shipping_country = db.Column(db.String(120), nullable=False, default='')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', back_populates='orders')
    items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    payment = db.relationship('Payment', back_populates='order', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Order {self.id}>'
