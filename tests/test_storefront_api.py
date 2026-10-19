from decimal import Decimal

from app.extensions import db
from app.models.categories import Category
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


def test_private_cart_requires_login(client):
    response = client.get('/api/cart')

    assert response.status_code == 401
    assert response.json['success'] is False


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
    })
    assert checkout.status_code == 201
    assert checkout.json['data']['total'] == '50.00'
    assert checkout.json['data']['payment'] == {
        'method': 'simulated_card',
        'status': 'pending',
    }
    assert checkout.json['data']['shipping_address']['recipient'] == 'Test Buyer'
    assert client.get('/api/cart').json['data']['count'] == 0

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
    })
    assert order.status_code == 201
    assert register(second_client, 'second@example.test').status_code == 201

    response = second_client.get(f"/api/orders/{order.json['data']['id']}")

    assert response.status_code == 404
