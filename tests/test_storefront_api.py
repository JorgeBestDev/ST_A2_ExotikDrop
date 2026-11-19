from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.extensions import db
from app.models.categories import Category
from app.models.drops import Drop
from app.models.inventory_reservations import InventoryReservation
from app.models.orders import Order
from app.models.payments import Payment
from app.models.products import Product


def create_product(app, stock=5):
    with app.app_context():
        category = Category(name='Sneakers')
        db.session.add(category)
        db.session.flush()
        product = Product(
            category_id=category.id,
            name='Test sneaker',
            description='Development test product',
            price=Decimal('25.00'),
            stock=stock,
            image_url='https://example.test/shoe.jpg',
            is_active=True,
        )
        db.session.add(product)
        db.session.commit()
        return product.id


def register(client, email='buyer@example.test'):
    return client.post('/api/auth/register', json={
        'full_name': 'Test Buyer',
        'email': email,
        'password': 'development-password',
    })


def create_address(client):
    return client.post('/api/account/addresses', json={
        'recipient': 'Test Buyer',
        'phone': '5550100',
        'line1': '123 Test Street',
        'line2': '',
        'city': 'Test City',
        'region': 'Test Region',
        'postal_code': '12345',
        'country': 'Test Country',
    })


def create_drop(app, name, status, starts_at, ends_at, with_product=True):
    with app.app_context():
        category = Category(name=f'{name} category')
        db.session.add(category)
        db.session.flush()
        drop = Drop(
            name=name,
            description=f'{name} description',
            status=status,
            starts_at=starts_at,
            ends_at=ends_at,
        )
        db.session.add(drop)
        db.session.flush()
        if with_product:
            db.session.add(Product(
                category_id=category.id,
                drop_id=drop.id,
                name=f'{name} product',
                description='Drop product preview',
                price=Decimal('180.00'),
                stock=4,
                image_url='https://example.test/drop.jpg',
                is_active=True,
            ))
        db.session.commit()
        return drop.id


def test_private_cart_requires_login(client):
    response = client.get('/api/cart')

    assert response.status_code == 401
    assert response.json['success'] is False


def test_customer_session_cookie_is_partitioned_for_cross_site_browsers(app, client):
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAMESITE='None',
        SESSION_COOKIE_PARTITIONED=True,
    )
    base_url = 'https://api.example.test'
    response = client.post('/api/auth/register', json={
        'full_name': 'Test Buyer',
        'email': 'partitioned-buyer@example.test',
        'password': 'development-password',
    }, base_url=base_url)

    cookie = response.headers['Set-Cookie']
    assert response.status_code == 201
    assert 'exitdrop_customer_session=' in cookie
    assert 'SameSite=None' in cookie
    assert 'Secure' in cookie
    assert 'Partitioned' in cookie
    assert client.get('/api/auth/me', base_url=base_url).status_code == 200


def test_guest_cart_merge_and_checkout_snapshot(app, client):
    product_id = create_product(app)
    assert register(client).status_code == 201

    merged = client.post('/api/cart/merge', json={
        'items': [{'product_id': product_id, 'quantity': 2}],
    })
    assert merged.status_code == 200
    assert merged.json['data']['count'] == 2
    assert merged.json['data']['subtotal'] == '50.00'

    address_response = create_address(client)
    assert address_response.status_code == 201
    address_id = address_response.json['data']['id']

    checkout = client.post('/api/orders', json={
        'address_id': address_id,
        'payment_method': 'simulated_card',
    }, headers={'Idempotency-Key': 'checkout-test-key'})
    assert checkout.status_code == 201
    assert checkout.json['data']['total'] == '50.00'
    assert checkout.json['data']['payment'] == {
        'method': 'simulated_card',
        'status': 'pending',
    }
    assert checkout.json['data']['shipping_address']['recipient'] == 'Test Buyer'
    assert client.get('/api/cart').json['data']['count'] == 0
    retry = client.post('/api/orders', json={
        'address_id': address_id,
        'payment_method': 'simulated_card',
    }, headers={'Idempotency-Key': 'checkout-test-key'})
    assert retry.status_code == 200
    assert retry.json['data']['id'] == checkout.json['data']['id']

    with app.app_context():
        product = db.session.get(Product, product_id)
        assert product.stock == 5

    payment = client.post(f"/api/orders/{checkout.json['data']['id']}/pay")
    assert payment.status_code == 200, payment.json
    assert payment.json['data']['status'] == 'paid'
    with app.app_context():
        product = db.session.get(Product, product_id)
        assert product.stock == 3

    orders = client.get('/api/orders')
    assert orders.status_code == 200
    assert len(orders.json['data']) == 1


def test_guest_cart_merge_rejects_overstock_without_partial_write(app, client):
    product_id = create_product(app, stock=2)
    assert register(client).status_code == 201

    response = client.post('/api/cart/merge', json={
        'items': [{'product_id': product_id, 'quantity': 3}],
    })

    assert response.status_code == 409
    assert client.get('/api/cart').json['data']['count'] == 0


def test_user_cannot_read_another_users_order(app):
    product_id = create_product(app)
    first_client = app.test_client()
    second_client = app.test_client()
    assert register(first_client, 'first@example.test').status_code == 201
    address_response = create_address(first_client)
    assert address_response.status_code == 201
    first_client.post('/api/cart/items', json={'product_id': product_id, 'quantity': 1})
    order = first_client.post('/api/orders', json={
        'address_id': address_response.json['data']['id'],
        'payment_method': 'simulated_card',
    }, headers={'Idempotency-Key': 'checkout-first-user'})
    assert order.status_code == 201
    assert register(second_client, 'second@example.test').status_code == 201

    response = second_client.get(f"/api/orders/{order.json['data']['id']}")

    assert response.status_code == 404


def test_drop_checkout_reserves_stock_until_demo_payment(app):
    now = datetime.now(timezone.utc)
    drop_id = create_drop(
        app,
        'Limited drop',
        'active',
        now - timedelta(hours=1),
        now + timedelta(hours=1),
    )
    with app.app_context():
        product_id = db.session.get(Drop, drop_id).products[0].id

    buyer = app.test_client()
    assert register(buyer, 'drop-buyer@example.test').status_code == 201
    address = create_address(buyer).json['data']
    assert buyer.post('/api/cart/items', json={'product_id': product_id, 'quantity': 3}).status_code == 200
    checkout = buyer.post('/api/orders', json={
        'address_id': address['id'],
        'payment_method': 'simulated_card',
    }, headers={'Idempotency-Key': 'drop-checkout-once'})

    assert checkout.status_code == 201
    assert checkout.json['data']['status'] == 'pending'
    assert checkout.json['data']['reservation']['status'] == 'active'

    with app.app_context():
        product = db.session.get(Product, product_id)
        assert product.stock == 4
        reservation = InventoryReservation.query.one()
        assert abs((reservation.expires_at - reservation.created_at).total_seconds() - 600) < 1

    assert buyer.post(
        '/api/cart/items',
        json={'product_id': product_id, 'quantity': 2},
    ).status_code == 409

    payment = buyer.post(f"/api/orders/{checkout.json['data']['id']}/pay")

    assert payment.status_code == 200, payment.json
    assert payment.json['data']['status'] == 'paid'
    assert buyer.get('/api/checkout/reservation').json['data']['reservation'] is None
    with app.app_context():
        assert db.session.get(Product, product_id).stock == 1
        assert InventoryReservation.query.one().status == 'consumed'


def test_expired_drop_reservation_releases_inventory_and_expires_order(app):
    now = datetime.now(timezone.utc)
    create_drop(
        app,
        'Expiring drop',
        'active',
        now - timedelta(hours=1),
        now + timedelta(hours=1),
    )
    with app.app_context():
        product_id = Drop.query.one().products[0].id

    buyer = app.test_client()
    assert register(buyer, 'expiring-buyer@example.test').status_code == 201
    address = create_address(buyer).json['data']
    buyer.post('/api/cart/items', json={'product_id': product_id, 'quantity': 4})
    checkout = buyer.post('/api/orders', json={
        'address_id': address['id'],
        'payment_method': 'simulated_card',
    }, headers={'Idempotency-Key': 'expiring-drop-checkout'})
    order_id = checkout.json['data']['id']

    with app.app_context():
        reservation = InventoryReservation.query.one()
        reservation.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.session.commit()

    response = buyer.get('/api/checkout/reservation')

    assert response.status_code == 200
    assert response.json['data']['reservation'] is None
    with app.app_context():
        assert db.session.get(Order, order_id).status == 'expired'
        assert Payment.query.one().status == 'expired'
        assert InventoryReservation.query.one().status == 'expired'


def test_featured_drop_returns_active_drop_and_its_active_products(app, client):
    now = datetime.now(timezone.utc)
    active_id = create_drop(
        app,
        'Current drop',
        'active',
        now - timedelta(hours=1),
        now + timedelta(hours=2),
    )
    create_drop(
        app,
        'Scheduled drop',
        'scheduled',
        now + timedelta(days=1),
        now + timedelta(days=2),
    )
    with app.app_context():
        drop = db.session.get(Drop, active_id)
        db.session.add(Product(
            category_id=drop.products[0].category_id,
            drop_id=active_id,
            name='Inactive catalog product',
            description='Should not be featured',
            price=Decimal('99.00'),
            stock=2,
            image_url='https://example.test/inactive.jpg',
            is_active=False,
        ))
        db.session.add(Product(
            category_id=drop.products[0].category_id,
            drop_id=None,
            name='Unassigned catalog product',
            description='Should not be featured',
            price=Decimal('75.00'),
            stock=6,
            image_url='https://example.test/unassigned.jpg',
            is_active=True,
        ))
        db.session.commit()

    response = client.get('/api/drops/featured')

    assert response.status_code == 200
    featured = response.json['data']
    assert featured['status'] == 'active'
    assert featured['drop']['id'] == active_id
    assert featured['drop']['starts_at'].endswith('+00:00')
    assert len(featured['products']) == 1
    assert featured['products'][0]['name'] == 'Current drop product'
    assert featured['products'][0]['drop_id'] == active_id
    assert featured['products'][0]['price'] == '180.00'
    assert featured['products'][0]['stock'] == 4
    assert featured['products'][0]['image_url'] == 'https://example.test/drop.jpg'


def test_featured_drop_falls_back_to_most_recent_ended_drop(app, client):
    now = datetime.now(timezone.utc)
    create_drop(
        app,
        'Older ended drop',
        'ended',
        now - timedelta(days=5),
        now - timedelta(days=4),
    )
    create_drop(
        app,
        'Latest ended drop',
        'ended',
        now - timedelta(days=2),
        now - timedelta(days=1),
    )
    most_recent_expired_id = create_drop(
        app,
        'Expired active drop',
        'active',
        now - timedelta(hours=2),
        now - timedelta(hours=1),
    )
    create_drop(
        app,
        'Future drop',
        'scheduled',
        now + timedelta(days=1),
        now + timedelta(days=2),
    )

    response = client.get('/api/drops/featured')

    assert response.status_code == 200
    assert response.json['data']['status'] == 'ended'
    assert response.json['data']['drop']['id'] == most_recent_expired_id


def test_featured_drop_returns_empty_when_there_is_no_active_or_ended_drop(app, client):
    now = datetime.now(timezone.utc)
    create_drop(
        app,
        'Future drop',
        'scheduled',
        now + timedelta(days=1),
        now + timedelta(days=2),
        with_product=False,
    )

    response = client.get('/api/drops/featured')

    assert response.status_code == 200
    assert response.json['data'] is None


def test_featured_drop_does_not_treat_a_future_active_drop_as_current(app, client):
    now = datetime.now(timezone.utc)
    create_drop(
        app,
        'Future active drop',
        'active',
        now + timedelta(hours=1),
        now + timedelta(hours=2),
        with_product=False,
    )

    response = client.get('/api/drops/featured')

    assert response.status_code == 200
    assert response.json['data'] is None
