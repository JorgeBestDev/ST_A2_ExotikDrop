from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app
from app.extensions import db
from app.models.categories import Category
from app.models.drops import Drop
from app.models.products import Product

PRODUCTS = (
    ('Sneakers', 'Air Jordan 1 Retro Low OG "Mocha"', '160.00', 'https://images.unsplash.com/photo-1552346154-21d32810aba3?auto=format&fit=crop&w=800&q=85'),
    ('Sneakers', 'adidas Samba OG "Cream Black"', '120.00', 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=85'),
    ('Hoodies', 'ExitDrop Washed Hoodie', '89.00', 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=800&q=85'),
    ('Pants', 'ExitDrop Cargo Pants "Brown"', '99.00', 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=800&q=85'),
    ('Hats & Accessories', 'ExitDrop Logo Cap', '39.00', 'https://images.unsplash.com/photo-1521369909029-2afed882baee?auto=format&fit=crop&w=800&q=85'),
    ('T-Shirts', 'ExitDrop District Tee', '45.00', 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=800&q=85'),
)
FEATURED_PRODUCT_NAMES = {'Air Jordan 1 Retro Low OG "Mocha"'}


def seed_database() -> None:
    app = create_app('development')
    with app.app_context():
        db.create_all()
        drop = Drop.query.filter_by(name='Just Landed').first()
        has_active_drop = Drop.query.filter_by(status='active').first() is not None
        if drop is None and not has_active_drop:
            now = datetime.now(timezone.utc)
            drop = Drop(
                name='Just Landed',
                description='The latest heat. Fresh styles. Limited quantities.',
                starts_at=now,
                ends_at=now + timedelta(days=30),
                status='active',
            )
            db.session.add(drop)

        categories = {}
        for name, _, _, _ in PRODUCTS:
            category = Category.query.filter_by(name=name).first()
            if category is None:
                category = Category(name=name, description=f'Explore our {name.lower()} collection.')
                db.session.add(category)
            categories[name] = category

        db.session.flush()
        for category_name, name, price, image_url in PRODUCTS:
            product = Product.query.filter_by(name=name).first()
            featured_product = name in FEATURED_PRODUCT_NAMES
            if product is None:
                db.session.add(Product(
                    category_id=categories[category_name].id,
                    drop_id=drop.id if drop and featured_product else None,
                    name=name,
                    description=f'{name} from the ExitDrop collection.',
                    price=Decimal(price),
                    stock=12,
                    image_url=image_url,
                    is_active=True,
                ))
            elif drop and featured_product and product.drop_id is None:
                product.drop_id = drop.id
            elif drop and not featured_product and product.drop_id == drop.id:
                product.drop_id = None

        db.session.commit()
        print(f'Development database ready: {Product.query.count()} products, {Category.query.count()} categories')


if __name__ == '__main__':
    seed_database()
