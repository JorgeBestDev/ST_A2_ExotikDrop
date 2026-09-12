from app.extensions import db


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    products = db.relationship('Product', back_populates='category', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Category {self.name}>'
