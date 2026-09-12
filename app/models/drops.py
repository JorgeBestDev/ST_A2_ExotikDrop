from datetime import datetime, timezone

from app.extensions import db


class Drop(db.Model):
    __tablename__ = 'drops'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    starts_at = db.Column(db.DateTime(timezone=True), nullable=False)
    ends_at = db.Column(db.DateTime(timezone=True), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='scheduled')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    products = db.relationship('Product', back_populates='drop', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Drop {self.name}>'
