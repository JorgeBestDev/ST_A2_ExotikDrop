from datetime import datetime, timezone

from app.extensions import db


class Cart(db.Model):
    __tablename__ = 'carts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', back_populates='carts')
    items = db.relationship('CartItem', back_populates='cart', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Cart {self.id}>'
