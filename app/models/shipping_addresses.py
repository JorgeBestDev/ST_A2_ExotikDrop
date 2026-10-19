from datetime import datetime, timezone

from app.extensions import db


class ShippingAddress(db.Model):
    __tablename__ = 'shipping_addresses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    recipient = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(40), nullable=False)
    line1 = db.Column(db.String(255), nullable=False)
    line2 = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(120), nullable=False)
    region = db.Column(db.String(120), nullable=False)
    postal_code = db.Column(db.String(30), nullable=False)
    country = db.Column(db.String(120), nullable=False)
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', back_populates='addresses')

    def __repr__(self):
        return f'<ShippingAddress {self.id} for user {self.user_id}>'
