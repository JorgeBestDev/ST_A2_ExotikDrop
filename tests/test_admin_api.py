from datetime import datetime, timedelta, timezone
from decimal import Decimal
import re

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models.categories import Category
from app.models.drops import Drop
from app.models.order_items import OrderItem
from app.models.orders import Order
from app.models.products import Product
from app.models.users import User


def create_admin(app, email='admin@example.test'):
    with app.app_context():
        user = User(
            email=email,
            full_name='Store Admin',
            password_hash=generate_password_hash('admin-password-123'),
            is_admin=True,
        )
        db.session.add(user)
        db.session.commit()
        return user.id


def captcha_login(client, email='admin@example.test', password='admin-password-123'):
    challenge = client.get('/api/admin/auth/captcha').json['data']
    left, right = map(int, re.search(r'(\d+) × (\d+)', challenge['question']).groups())
    return client.post('/api/admin/auth/login', json={
        'email': email,
        'password': password,
        'challenge_id': challenge['challenge_id'],
        'captcha_answer': str(left * right),
    })


def test_admin_login_requires_captcha_and_admin_role(app):
    create_admin(app)
    client = app.test_client()

    assert client.get('/api/admin/dashboard').status_code == 401
    regular_login = client.post('/api/auth/login', json={
        'email': 'admin@example.test',
        'password': 'admin-password-123',
    })
    assert regular_login.status_code == 200
    assert client.get('/api/admin/dashboard').status_code == 403
    assert client.get('/api/users').status_code == 403
    client.post('/api/auth/logout')

    captcha = client.get('/api/admin/auth/captcha').json['data']
    left, right = map(int, re.search(r'(\d+) × (\d+)', captcha['question']).groups())
    response = client.post('/api/admin/auth/login', json={
        'email': 'admin@example.test',
        'password': 'admin-password-123',
        'challenge_id': captcha['challenge_id'],
        'captcha_answer': str(left * right),
    })
    assert response.status_code == 200
    assert client.get('/api/admin/auth/me').status_code == 200
    assert client.post('/api/admin/auth/login', json={
        'email': 'admin@example.test',
        'password': 'admin-password-123',
        'challenge_id': captcha['challenge_id'],
        'captcha_answer': str(left * right),
    }).status_code == 400


def test_captcha_is_consumed_on_wrong_answer(app):
    create_admin(app)
    client = app.test_client()
    challenge = client.get('/api/admin/auth/captcha').json['data']
    payload = {
        'email': 'admin@example.test',
        'password': 'admin-password-123',
        'challenge_id': challenge['challenge_id'],
        'captcha_answer': 'wrong',
    }

    assert client.post('/api/admin/auth/login', json=payload).status_code == 400
    assert client.post('/api/admin/auth/login', json=payload).status_code == 400


def test_admin_login_limits_failed_attempts_per_ip(app):
    create_admin(app)
    client = app.test_client()
    for _ in range(5):
        challenge = client.get('/api/admin/auth/captcha').json['data']
        left, right = map(int, re.search(r'(\d+) × (\d+)', challenge['question']).groups())
        response = client.post('/api/admin/auth/login', json={
            'email': 'admin@example.test',
            'password': 'incorrect-password',
            'challenge_id': challenge['challenge_id'],
            'captcha_answer': str(left * right),
        })
        assert response.status_code == 401

    challenge = client.get('/api/admin/auth/captcha').json['data']
    left, right = map(int, re.search(r'(\d+) × (\d+)', challenge['question']).groups())
    response = client.post('/api/admin/auth/login', json={
        'email': 'admin@example.test',
        'password': 'admin-password-123',
        'challenge_id': challenge['challenge_id'],
        'captcha_answer': str(left * right),
    })
    assert response.status_code == 429


def test_dashboard_aggregates_monthly_orders_best_product_and_latest_drop(app, client):
    create_admin(app)
    with app.app_context():
        now = datetime.now(timezone.utc)
        category = Category(name='Sneakers')
        drop = Drop(
            name='Night Shift',
            description='Limited release',
            starts_at=now - timedelta(hours=2),
            ends_at=now + timedelta(hours=3),
            status='active',
        )
        db.session.add_all([category, drop])
        db.session.flush()
        drop_id = drop.id
        product = Product(
            category_id=category.id,
            drop_id=drop.id,
            name='Night Runner',
            price=Decimal('80.00'),
            stock=7,
            is_active=True,
        )
        user = User(
            email='buyer@example.test',
            full_name='Buyer',
            password_hash=generate_password_hash('buyer-password'),
        )
        db.session.add_all([product, user])
        db.session.flush()
        order = Order(user_id=user.id, total=Decimal('160.00'), status='pending', created_at=now)
        db.session.add(order)
        db.session.flush()
        db.session.add(OrderItem(
            order_id=order.id,
            product_id=product.id,
            drop_id=drop.id,
            quantity=2,
            unit_price=Decimal('80.00'),
            total_price=Decimal('160.00'),
        ))
        product_id = product.id
        db.session.commit()

    assert captcha_login(client).status_code == 200
    response = client.get('/api/admin/dashboard')
    assert response.status_code == 200
    data = response.json['data']
    assert data['month'].startswith(datetime.now(timezone.utc).strftime('%Y-%m'))
    assert data['monthly_sales'] == 160.0
    assert data['best_selling_product'] == {
        'id': product_id,
        'name': 'Night Runner',
        'units_sold': 2,
        'revenue': 160.0,
    }
    assert data['latest_drop']['name'] == 'Night Shift'
    assert data['latest_drop']['sales'] == 160.0
    assert data['latest_drop']['remaining_units'] == 7
    assert 0 < data['latest_drop']['remaining_seconds'] <= 3 * 60 * 60

    with app.app_context():
        db.session.get(Product, product_id).drop_id = None
        db.session.commit()
    assert client.get('/api/admin/dashboard').json['data']['latest_drop']['sales'] == 160.0
    assert client.delete(f'/api/admin/drops/{drop_id}').status_code == 409


def test_admin_management_preserves_order_history_and_last_admin(app, client):
    admin_id = create_admin(app)
    with app.app_context():
        category = Category(name='Apparel')
        drop = Drop(
            name='Archive',
            starts_at=datetime.now(timezone.utc) - timedelta(days=1),
            ends_at=datetime.now(timezone.utc) + timedelta(days=1),
            status='active',
        )
        db.session.add_all([category, drop])
        db.session.flush()
        product = Product(
            category_id=category.id,
            drop_id=drop.id,
            name='Archive Tee',
            price=Decimal('30.00'),
            stock=4,
            is_active=True,
        )
        db.session.add(product)
        db.session.commit()
        product_id = product.id
        drop_id = drop.id

    assert captcha_login(client).status_code == 200
    assert client.post('/api/admin/users', json=[]).status_code == 400
    assert client.post('/api/admin/products', json=[]).status_code == 400
    assert client.post('/api/admin/drops', json=[]).status_code == 400
    assert client.delete(f'/api/admin/users/{admin_id}').status_code == 409
    assert client.delete(f'/api/admin/products/{product_id}').status_code == 200
    assert client.delete(f'/api/admin/drops/{drop_id}').status_code == 409
    assert client.get('/api/products').json['count'] == 0
    assert client.get('/api/admin/products').json['data'][0]['is_active'] is False


def test_admin_can_create_and_edit_users_products_and_drops(app, client):
    create_admin(app)
    with app.app_context():
        category = Category(name='Accessories')
        db.session.add(category)
        db.session.commit()
        category_id = category.id

    assert captcha_login(client).status_code == 200
    drop_response = client.post('/api/admin/drops', json={
        'name': 'Spring Capsule',
        'description': 'Seasonal release',
        'starts_at': (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        'ends_at': (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        'status': 'scheduled',
    })
    assert drop_response.status_code == 201
    drop_id = drop_response.json['data']['id']

    product_response = client.post('/api/admin/products', json={
        'category_id': category_id,
        'drop_id': drop_id,
        'name': 'Canvas Bag',
        'price': '45.00',
        'stock': 12,
        'description': 'Everyday carry',
        'image_url': None,
    })
    assert product_response.status_code == 201
    product_id = product_response.json['data']['id']
    product_update = client.put(f'/api/admin/products/{product_id}', json={
        'category_id': category_id,
        'drop_id': drop_id,
        'name': 'Canvas Bag XL',
        'price': '55.00',
        'stock': 9,
        'description': 'Updated size',
        'image_url': None,
        'is_active': True,
    })
    assert product_update.status_code == 200
    assert product_update.json['data']['name'] == 'Canvas Bag XL'
    assert product_update.json['data']['stock'] == 9

    user_response = client.post('/api/admin/users', json={
        'full_name': 'New Customer',
        'email': 'new-customer@example.com',
        'password': 'customer-password',
    })
    assert user_response.status_code == 201
    user_id = user_response.json['data']['id']
    updated_user = client.put(f'/api/admin/users/{user_id}', json={
        'full_name': 'Updated Customer',
        'email': 'new-customer@example.com',
        'is_admin': False,
    })
    assert updated_user.status_code == 200
    assert updated_user.json['data']['full_name'] == 'Updated Customer'
    assert updated_user.json['data']['is_active'] is True
    assert client.delete(f'/api/admin/users/{user_id}').status_code == 200
    inactive_client = app.test_client()
    assert inactive_client.post('/api/auth/login', json={
        'email': 'new-customer@example.test',
        'password': 'customer-password',
    }).status_code == 401


def test_admin_create_cli_provisions_an_account(app):
    result = app.test_cli_runner().invoke(args=[
        'admin-create',
        '--email', 'bootstrapped@example.com',
        '--name', 'Bootstrapped Admin',
        '--password', 'bootstrap-password',
    ])

    assert result.exit_code == 0, result.output
    with app.app_context():
        user = User.query.filter_by(email='bootstrapped@example.com').one()
        assert user.is_admin is True
        assert user.is_active is True


def test_production_requires_a_configured_secret_key(monkeypatch):
    monkeypatch.delenv('SECRET_KEY', raising=False)

    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        create_app('production')


def test_production_forces_secure_session_cookies(monkeypatch):
    monkeypatch.setenv('SECRET_KEY', 'a-strong-random-secret-that-is-at-least-32-chars')
    monkeypatch.setenv('SESSION_COOKIE_SECURE', 'False')

    production_app = create_app('production')

    assert production_app.config['DEBUG'] is False
    assert production_app.config['SESSION_COOKIE_SECURE'] is True
