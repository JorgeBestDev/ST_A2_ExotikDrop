from decimal import Decimal
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.cart_items import CartItem
from app.models.carts import Cart
from app.models.orders import Order
from app.models.order_items import OrderItem
from app.models.payments import Payment
from app.models.products import Product
from app.models.shipping_addresses import ShippingAddress
from app.models.users import User
from app.models.inventory_reservations import InventoryReservation, InventoryReservationItem
from app.services.inventory import as_utc, available_stock, expire_reservations, reserved_quantities
from app.services.transactions import rollback_on_error

bp = Blueprint('storefront', __name__, url_prefix='/api')
ADDRESS_FIELDS = (
    'recipient',
    'phone',
    'line1',
    'line2',
    'city',
    'region',
    'postal_code',
    'country',
)
REQUIRED_ADDRESS_FIELDS = tuple(field for field in ADDRESS_FIELDS if field != 'line2')


def serialize_user(user):
    return {
        'id': user.id,
        'email': user.email,
        'full_name': user.full_name,
        'is_admin': user.is_admin,
    }


def serialize_address(address):
    return {
        'id': address.id,
        **{field: getattr(address, field) for field in ADDRESS_FIELDS},
        'is_default': address.is_default,
    }


def get_or_create_cart(user):
    cart = Cart.query.filter_by(user_id=user.id).first()
    if cart is None:
        cart = Cart(user_id=user.id)
        db.session.add(cart)
        db.session.flush()
    return cart


def serialize_cart(cart):
    items = []
    subtotal = Decimal('0.00')
    reserved = reserved_quantities(item.product_id for item in cart.items)
    for item in cart.items:
        product = item.product
        line_total = product.price * item.quantity
        subtotal += line_total
        items.append({
            'id': item.id,
            'product_id': product.id,
            'name': product.name,
            'price': f'{product.price:.2f}',
            'image_url': product.image_url,
            'quantity': item.quantity,
            'stock': available_stock(product, reserved=reserved.get(product.id, 0)),
            'line_total': f'{line_total:.2f}',
        })
    return {'id': cart.id, 'items': items, 'subtotal': f'{subtotal:.2f}', 'count': sum(item['quantity'] for item in items)}


def address_payload(data, partial=False):
    result = {}
    required = REQUIRED_ADDRESS_FIELDS if not partial else ()
    for field in ADDRESS_FIELDS:
        value = data.get(field)
        if field in required and (not isinstance(value, str) or not value.strip()):
            return None, f'{field} es obligatorio'
        if value is not None:
            if not isinstance(value, str):
                return None, f'{field} debe ser texto'
            result[field] = value.strip() or None if field == 'line2' else value.strip()
    return result, None


@bp.post('/auth/register')
@rollback_on_error
def register():
    data = request.get_json(silent=True) or {}
    full_name = data.get('full_name')
    email = data.get('email')
    password = data.get('password')
    if not all(isinstance(value, str) and value.strip() for value in (full_name, email, password)):
        return jsonify(success=False, message='Nombre, email y contraseña son obligatorios'), 400
    email = email.strip().lower()
    if len(password) < 8:
        return jsonify(success=False, message='La contraseña debe tener al menos 8 caracteres'), 400
    if User.query.filter_by(email=email).first():
        return jsonify(success=False, message='El email ya está registrado'), 409

    user = User(email=email, full_name=full_name.strip(), password_hash=generate_password_hash(password))
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(success=False, message='El email ya está registrado'), 409
    login_user(user)
    return jsonify(success=True, data=serialize_user(user)), 201


@bp.post('/auth/login')
@rollback_on_error
def login():
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    password = data.get('password')
    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify(success=False, message='Email y contraseña son obligatorios'), 400
    user = User.query.filter_by(email=email.strip().lower(), is_active=True).first()
    if user is None or not check_password_hash(user.password_hash, password):
        return jsonify(success=False, message='Email o contraseña incorrectos'), 401
    login_user(user)
    return jsonify(success=True, data=serialize_user(user)), 200


@bp.post('/auth/logout')
@login_required
@rollback_on_error
def logout():
    logout_user()
    return jsonify(success=True), 200


@bp.get('/auth/me')
@login_required
def get_current_user():
    return jsonify(success=True, data=serialize_user(current_user)), 200


@bp.put('/account/profile')
@login_required
@rollback_on_error
def update_profile():
    data = request.get_json(silent=True) or {}
    full_name = data.get('full_name')
    email = data.get('email')
    if not isinstance(full_name, str) or not full_name.strip() or not isinstance(email, str) or not email.strip():
        return jsonify(success=False, message='Nombre y email son obligatorios'), 400
    email = email.strip().lower()
    duplicate = User.query.filter(User.email == email, User.id != current_user.id).first()
    if duplicate:
        return jsonify(success=False, message='El email ya está registrado'), 409
    current_user.full_name = full_name.strip()
    current_user.email = email
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(success=False, message='El email ya está registrado'), 409
    return jsonify(success=True, data=serialize_user(current_user)), 200


@bp.put('/account/password')
@login_required
@rollback_on_error
def update_password():
    data = request.get_json(silent=True) or {}
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    if not isinstance(current_password, str) or not isinstance(new_password, str):
        return jsonify(success=False, message='Debes proporcionar ambas contraseñas'), 400
    if not check_password_hash(current_user.password_hash, current_password):
        return jsonify(success=False, message='La contraseña actual es incorrecta'), 400
    if len(new_password) < 8:
        return jsonify(success=False, message='La nueva contraseña debe tener al menos 8 caracteres'), 400
    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    return jsonify(success=True, message='Contraseña actualizada'), 200


@bp.route('/account/addresses', methods=['GET', 'POST'])
@login_required
@rollback_on_error
def account_addresses():
    if request.method == 'GET':
        addresses = ShippingAddress.query.filter_by(user_id=current_user.id).order_by(ShippingAddress.is_default.desc(), ShippingAddress.id.asc()).all()
        return jsonify(success=True, data=[serialize_address(address) for address in addresses]), 200

    data = request.get_json(silent=True) or {}
    values, error = address_payload(data)
    if error:
        return jsonify(success=False, message=error), 400
    is_default = bool(data.get('is_default')) or not ShippingAddress.query.filter_by(user_id=current_user.id).first()
    if is_default:
        ShippingAddress.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
    address = ShippingAddress(user_id=current_user.id, is_default=is_default, **values)
    db.session.add(address)
    db.session.commit()
    return jsonify(success=True, data=serialize_address(address)), 201


@bp.route('/account/addresses/<int:address_id>', methods=['PUT', 'DELETE'])
@login_required
@rollback_on_error
def edit_account_address(address_id):
    address = ShippingAddress.query.filter_by(id=address_id, user_id=current_user.id).first()
    if address is None:
        return jsonify(success=False, message='Dirección no encontrada'), 404

    if request.method == 'DELETE':
        was_default = address.is_default
        db.session.delete(address)
        db.session.flush()
        if was_default:
            next_address = ShippingAddress.query.filter_by(user_id=current_user.id).order_by(ShippingAddress.id.asc()).first()
            if next_address:
                next_address.is_default = True
        db.session.commit()
        return jsonify(success=True), 200

    data = request.get_json(silent=True) or {}
    values, error = address_payload(data, partial=True)
    if error:
        return jsonify(success=False, message=error), 400
    make_default = bool(data.get('is_default'))
    if make_default:
        ShippingAddress.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
        address.is_default = True
    for field, value in values.items():
        setattr(address, field, value)
    db.session.commit()
    return jsonify(success=True, data=serialize_address(address)), 200


@bp.get('/account/payment-methods')
@login_required
def account_payment_methods():
    methods = db.session.execute(
        select(Payment.method, Payment.status)
        .join(Order, Payment.order_id == Order.id)
        .where(Order.user_id == current_user.id)
        .distinct()
    ).all()
    return jsonify(success=True, data=[{'method': method, 'status': status} for method, status in methods]), 200


@bp.route('/cart', methods=['GET'])
@login_required
@rollback_on_error
def get_cart():
    cart = get_or_create_cart(current_user)
    db.session.commit()
    return jsonify(success=True, data=serialize_cart(cart)), 200


@bp.post('/cart/items')
@login_required
@rollback_on_error
def add_cart_item():
    data = request.get_json(silent=True) or {}
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    if not isinstance(product_id, int) or isinstance(product_id, bool) or not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
        return jsonify(success=False, message='Producto y cantidad válida son obligatorios'), 400
    product = db.session.get(Product, product_id)
    if product is None or not product.is_active:
        return jsonify(success=False, message='Producto no disponible'), 404
    cart = get_or_create_cart(current_user)
    item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
    resulting_quantity = quantity + (item.quantity if item else 0)
    if resulting_quantity > available_stock(product):
        return jsonify(success=False, message='La cantidad solicitada supera el inventario disponible'), 409
    if item:
        item.quantity = resulting_quantity
    else:
        db.session.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=quantity))
    db.session.commit()
    return jsonify(success=True, data=serialize_cart(cart)), 200


@bp.put('/cart/items/<int:item_id>')
@login_required
@rollback_on_error
def update_cart_item(item_id):
    data = request.get_json(silent=True) or {}
    quantity = data.get('quantity')
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
        return jsonify(success=False, message='La cantidad debe ser un entero positivo'), 400
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id if cart else -1).first()
    if item is None:
        return jsonify(success=False, message='Producto no encontrado en el carrito'), 404
    if quantity > available_stock(item.product):
        return jsonify(success=False, message='La cantidad solicitada supera el inventario disponible'), 409
    item.quantity = quantity
    db.session.commit()
    return jsonify(success=True, data=serialize_cart(cart)), 200


@bp.delete('/cart/items/<int:item_id>')
@login_required
@rollback_on_error
def delete_cart_item(item_id):
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id if cart else -1).first()
    if item is None:
        return jsonify(success=False, message='Producto no encontrado en el carrito'), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify(success=True, data=serialize_cart(cart)), 200


@bp.post('/cart/merge')
@login_required
@rollback_on_error
def merge_guest_cart():
    data = request.get_json(silent=True) or {}
    guest_items = data.get('items')
    if not isinstance(guest_items, list):
        return jsonify(success=False, message='items debe ser una lista'), 400
    parsed = {}
    for entry in guest_items:
        if not isinstance(entry, dict):
            return jsonify(success=False, message='Cada producto debe incluir id y cantidad'), 400
        product_id = entry.get('product_id')
        quantity = entry.get('quantity')
        if not isinstance(product_id, int) or isinstance(product_id, bool) or not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
            return jsonify(success=False, message='Cada producto debe incluir id y cantidad válida'), 400
        parsed[product_id] = parsed.get(product_id, 0) + quantity

    cart = get_or_create_cart(current_user)
    prepared = []
    for product_id, quantity in parsed.items():
        product = db.session.get(Product, product_id)
        if product is None or not product.is_active:
            return jsonify(success=False, message=f'Producto {product_id} ya no está disponible'), 409
        current_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
        total_quantity = quantity + (current_item.quantity if current_item else 0)
        if total_quantity > available_stock(product):
            return jsonify(success=False, message=f'Inventario insuficiente para {product.name}'), 409
        prepared.append((product, current_item, total_quantity, quantity))

    for product, current_item, total_quantity, quantity in prepared:
        if current_item:
            current_item.quantity = total_quantity
        else:
            db.session.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=quantity))
    db.session.commit()
    return jsonify(success=True, data=serialize_cart(cart)), 200


@bp.post('/orders')
@login_required
@rollback_on_error
def checkout():
    data = request.get_json(silent=True) or {}
    address_id = data.get('address_id')
    checkout_key = request.headers.get('Idempotency-Key') or data.get('checkout_key')
    if not isinstance(address_id, int) or isinstance(address_id, bool):
        return jsonify(success=False, message='Selecciona una dirección de envío'), 400
    if data.get('payment_method') != 'simulated_card':
        return jsonify(success=False, message='Método de pago provisional no válido'), 400
    if not isinstance(checkout_key, str) or not checkout_key.strip() or len(checkout_key.strip()) > 64:
        return jsonify(success=False, message='Se requiere una clave de idempotencia válida'), 400

    checkout_key = checkout_key.strip()
    user = User.query.filter_by(id=current_user.id).with_for_update().first()
    now = datetime.now(timezone.utc)
    expire_reservations(user.id, now)
    existing_order = Order.query.filter_by(user_id=user.id, checkout_key=checkout_key).first()
    if existing_order is not None:
        return jsonify(success=True, data=serialize_order(existing_order)), 200

    active_reservation = InventoryReservation.query.filter_by(
        user_id=user.id,
        status='active',
    ).with_for_update().first()
    if active_reservation is not None:
        active_reservation.status = 'released'
        if active_reservation.order.status == 'pending':
            active_reservation.order.status = 'cancelled'
        if active_reservation.order.payment and active_reservation.order.payment.status == 'pending':
            active_reservation.order.payment.status = 'cancelled'

    address = ShippingAddress.query.filter_by(id=address_id, user_id=user.id).first()
    if address is None:
        return jsonify(success=False, message='Dirección de envío no encontrada'), 404
    cart = Cart.query.filter_by(user_id=user.id).with_for_update().first()
    if cart is None or not cart.items:
        return jsonify(success=False, message='El carrito está vacío'), 400

    cart_items = sorted(cart.items, key=lambda item: item.product_id)
    product_ids = [item.product_id for item in cart_items]
    products = db.session.execute(
        select(Product)
        .where(Product.id.in_(product_ids), Product.is_active.is_(True))
        .order_by(Product.id.asc())
        .with_for_update()
    ).scalars().all()
    products_by_id = {product.id: product for product in products}
    if len(products_by_id) != len(set(product_ids)):
        return jsonify(success=False, message='Un producto del carrito ya no está disponible'), 409

    reserved = reserved_quantities(product_ids, now)
    for cart_item in cart_items:
        product = products_by_id[cart_item.product_id]
        available = product.stock - reserved.get(product.id, 0)
        if cart_item.quantity > available:
            return jsonify(success=False, message=f'Inventario insuficiente para {product.name}'), 409

    order = Order(
        user_id=user.id,
        total=Decimal('0.00'),
        status='pending',
        checkout_key=checkout_key,
        shipping_recipient=address.recipient,
        shipping_phone=address.phone,
        shipping_line1=address.line1,
        shipping_line2=address.line2,
        shipping_city=address.city,
        shipping_region=address.region,
        shipping_postal_code=address.postal_code,
        shipping_country=address.country,
    )
    total = Decimal('0.00')
    reserved_items = []
    for cart_item in cart_items:
        product = products_by_id[cart_item.product_id]
        line_total = product.price * cart_item.quantity
        total += line_total
        order.items.append(OrderItem(
            product_id=product.id,
            drop_id=product.drop_id,
            quantity=cart_item.quantity,
            unit_price=product.price,
            total_price=line_total,
        ))
        if product.drop_id is not None:
            reserved_items.append((product.id, cart_item.quantity))
    order.total = total
    db.session.add(order)
    db.session.flush()
    order.payment = Payment(
        order_id=order.id,
        method='simulated_card',
        amount=total,
        status='pending',
    )
    if reserved_items:
        order.inventory_reservation = InventoryReservation(
            user_id=user.id,
            order_id=order.id,
            expires_at=now + timedelta(minutes=10),
            status='active',
        )
        order.inventory_reservation.items = [
            InventoryReservationItem(product_id=product_id, quantity=quantity)
            for product_id, quantity in reserved_items
        ]
    for cart_item in cart_items:
        db.session.delete(cart_item)
    db.session.flush()
    return jsonify(success=True, data=serialize_order(order)), 201


def serialize_order(order):
    return {
        'id': order.id,
        'total': f'{order.total:.2f}',
        'status': order.status,
        'created_at': order.created_at.isoformat() if order.created_at else None,
        'shipping_address': {
            'recipient': order.shipping_recipient,
            'phone': order.shipping_phone,
            'line1': order.shipping_line1,
            'line2': order.shipping_line2,
            'city': order.shipping_city,
            'region': order.shipping_region,
            'postal_code': order.shipping_postal_code,
            'country': order.shipping_country,
        },
        'items': [{
            'product_id': item.product_id,
            'name': item.product.name,
            'image_url': item.product.image_url,
            'quantity': item.quantity,
            'unit_price': f'{item.unit_price:.2f}',
            'total_price': f'{item.total_price:.2f}',
        } for item in order.items],
        'payment': {
            'method': order.payment.method,
            'status': order.payment.status,
        } if order.payment else None,
        'reservation': {
            'status': order.inventory_reservation.status,
            'expires_at': as_utc(order.inventory_reservation.expires_at).isoformat(),
        } if order.inventory_reservation else None,
    }


@bp.get('/checkout/reservation')
@login_required
@rollback_on_error
def get_current_reservation():
    now = datetime.now(timezone.utc)
    User.query.filter_by(id=current_user.id).with_for_update().first()
    expire_reservations(current_user.id, now)
    reservation = InventoryReservation.query.filter_by(
        user_id=current_user.id,
        status='active',
    ).filter(InventoryReservation.expires_at > now).first()
    return jsonify(success=True, data={
        'reservation': {
            'order_id': reservation.order_id,
            'expires_at': as_utc(reservation.expires_at).isoformat(),
        } if reservation else None,
        'server_time': now.isoformat(),
    }), 200


@bp.post('/orders/<int:order_id>/pay')
@login_required
@rollback_on_error
def confirm_simulated_payment(order_id):
    now = datetime.now(timezone.utc)
    User.query.filter_by(id=current_user.id).with_for_update().first()
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).with_for_update().first()
    if order is None:
        return jsonify(success=False, message='Pedido no encontrado'), 404
    if order.status == 'paid' and order.payment and order.payment.status == 'completed':
        return jsonify(success=True, data=serialize_order(order)), 200
    if order.status != 'pending' or order.payment is None or order.payment.status != 'pending':
        return jsonify(success=False, message='Este pedido ya no puede pagarse'), 409

    reservation = InventoryReservation.query.filter_by(order_id=order.id).with_for_update().first()
    if reservation is not None and (
        reservation.status != 'active' or as_utc(reservation.expires_at) <= now
    ):
        if reservation.status == 'active':
            reservation.status = 'expired'
        order.status = 'expired'
        order.payment.status = 'expired'
        db.session.commit()
        return jsonify(success=False, message='El tiempo para pagar esta reserva terminó'), 410

    order_items = sorted(order.items, key=lambda item: item.product_id)
    product_ids = [item.product_id for item in order_items]
    products = db.session.execute(
        select(Product)
        .where(Product.id.in_(product_ids))
        .order_by(Product.id.asc())
        .with_for_update()
    ).scalars().all()
    products_by_id = {product.id: product for product in products}
    unavailable = next(
        (
            products_by_id[item.product_id].name
            if item.product_id in products_by_id
            else f'producto #{item.product_id}'
            for item in order_items
            if item.product_id not in products_by_id
            or not products_by_id[item.product_id].is_active
            or products_by_id[item.product_id].stock < item.quantity
        ),
        None,
    )
    if unavailable is not None:
        if reservation is not None:
            reservation.status = 'released'
        order.status = 'cancelled'
        order.payment.status = 'failed'
        db.session.commit()
        return jsonify(success=False, message=f'Inventario insuficiente para {unavailable}; el pedido fue cancelado'), 409

    for item in order_items:
        products_by_id[item.product_id].stock -= item.quantity
    if reservation is not None:
        reservation.status = 'consumed'
    order.status = 'paid'
    order.payment.status = 'completed'
    db.session.commit()
    return jsonify(success=True, data=serialize_order(order)), 200


@bp.post('/orders/<int:order_id>/cancel')
@login_required
@rollback_on_error
def cancel_order_reservation(order_id):
    User.query.filter_by(id=current_user.id).with_for_update().first()
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).with_for_update().first()
    if order is None:
        return jsonify(success=False, message='Pedido no encontrado'), 404
    if order.status == 'paid':
        return jsonify(success=False, message='Un pedido pagado no se puede cancelar desde el checkout'), 409
    if order.status == 'cancelled':
        return jsonify(success=True, data=serialize_order(order)), 200
    if order.status == 'pending':
        order.status = 'cancelled'
        if order.payment and order.payment.status == 'pending':
            order.payment.status = 'cancelled'
        if order.inventory_reservation and order.inventory_reservation.status == 'active':
            order.inventory_reservation.status = 'released'
    db.session.commit()
    return jsonify(success=True, data=serialize_order(order)), 200
