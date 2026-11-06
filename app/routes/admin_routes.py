from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import hmac
import secrets
from uuid import uuid4
from functools import wraps

from flask import Blueprint, current_app, jsonify, request, session
from flask_login import current_user, login_required, login_user, logout_user
from email_validator import EmailNotValidError, validate_email
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.admin_captcha_challenges import AdminCaptchaChallenge
from app.models.categories import Category
from app.models.drops import Drop
from app.models.order_items import OrderItem
from app.models.orders import Order
from app.models.products import Product
from app.models.users import User

bp = Blueprint('admin', __name__, url_prefix='/api/admin')
CAPTCHA_LIFETIME = timedelta(minutes=3)
LOGIN_FAILURE_WINDOW = timedelta(minutes=15)
MAX_LOGIN_FAILURES = 5
CAPTCHA_REQUEST_WINDOW = timedelta(minutes=1)
MAX_CAPTCHA_REQUESTS = 20
ALLOWED_DROP_STATUSES = {'scheduled', 'active', 'ended', 'cancelled'}


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin or not session.get('admin_authenticated'):
            return jsonify(success=False, message='No tienes permiso para acceder al panel administrativo'), 403
        return view(*args, **kwargs)

    return wrapped


def to_utc_iso(value):
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def serialize_user(user):
    return {
        'id': user.id,
        'email': user.email,
        'full_name': user.full_name,
        'is_admin': user.is_admin,
        'is_active': user.is_active,
        'created_at': to_utc_iso(user.created_at),
    }


def serialize_drop(drop):
    return {
        'id': drop.id,
        'name': drop.name,
        'description': drop.description,
        'starts_at': to_utc_iso(drop.starts_at),
        'ends_at': to_utc_iso(drop.ends_at),
        'status': drop.status,
        'created_at': to_utc_iso(drop.created_at),
    }


def serialize_product(product):
    return {
        'id': product.id,
        'category_id': product.category_id,
        'category': product.category.name if product.category else None,
        'drop_id': product.drop_id,
        'drop': product.drop.name if product.drop else None,
        'name': product.name,
        'description': product.description,
        'price': str(product.price),
        'stock': product.stock,
        'image_url': product.image_url,
        'is_active': product.is_active,
        'created_at': product.created_at.isoformat() if product.created_at else None,
    }


def challenge_digest(challenge_id, answer):
    return hashlib.sha256(f'{challenge_id}:{answer}'.encode('utf-8')).hexdigest()


def request_fingerprint():
    address = request.remote_addr or 'unknown'
    secret = current_app.config['SECRET_KEY'].encode('utf-8')
    return hmac.new(secret, address.encode('utf-8'), hashlib.sha256).hexdigest()


def request_object():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def normalized_email(value):
    if not isinstance(value, str):
        return None
    try:
        return validate_email(value.strip(), check_deliverability=False).normalized
    except EmailNotValidError:
        return None


@bp.get('/auth/captcha')
def get_admin_captcha():
    now = datetime.now(timezone.utc)
    expiration = now - LOGIN_FAILURE_WINDOW
    AdminCaptchaChallenge.query.filter(
        (AdminCaptchaChallenge.created_at < expiration)
        | (AdminCaptchaChallenge.consumed.is_(True) & AdminCaptchaChallenge.login_failed.is_(False))
    ).delete(synchronize_session=False)
    fingerprint = request_fingerprint()
    recent_challenges = AdminCaptchaChallenge.query.filter(
        AdminCaptchaChallenge.client_fingerprint == fingerprint,
        AdminCaptchaChallenge.created_at >= now - CAPTCHA_REQUEST_WINDOW,
    ).count()
    if recent_challenges >= MAX_CAPTCHA_REQUESTS:
        db.session.commit()
        return jsonify(success=False, message='Solicitaste demasiados CAPTCHAs; inténtalo de nuevo más tarde'), 429

    left = secrets.randbelow(8) + 2
    right = secrets.randbelow(8) + 2
    challenge_id = str(uuid4())
    challenge = AdminCaptchaChallenge(
        id=challenge_id,
        answer_hash=challenge_digest(challenge_id, str(left * right)),
        client_fingerprint=fingerprint,
    )
    db.session.add(challenge)
    db.session.commit()
    return jsonify(success=True, data={
        'challenge_id': challenge_id,
        'question': f'¿Cuánto es {left} × {right}?',
    }), 200


@bp.post('/auth/login')
def admin_login():
    data = request_object()
    if data is None:
        return jsonify(success=False, message='El cuerpo debe ser un objeto JSON'), 400
    challenge_id = data.get('challenge_id')
    answer = data.get('captcha_answer')
    email = data.get('email')
    password = data.get('password')
    if not all(isinstance(value, str) and value.strip() for value in (challenge_id, answer, email, password)):
        return jsonify(success=False, message='Completa el CAPTCHA, el email y la contraseña'), 400
    if len(challenge_id) > 36 or len(answer.strip()) > 2 or not answer.strip().isdigit():
        return jsonify(success=False, message='El CAPTCHA no es válido'), 400

    challenge = db.session.get(AdminCaptchaChallenge, challenge_id)
    if challenge is None or challenge.consumed:
        return jsonify(success=False, message='El CAPTCHA expiró; solicita uno nuevo'), 400
    created_at = challenge.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    challenge.consumed = True
    db.session.commit()

    expected_hash = challenge_digest(challenge_id, answer.strip())
    captcha_valid = (
        datetime.now(timezone.utc) - created_at <= CAPTCHA_LIFETIME
        and hmac.compare_digest(challenge.answer_hash, expected_hash)
    )
    if not captcha_valid:
        challenge.login_failed = True
        challenge.client_fingerprint = request_fingerprint()
        db.session.commit()
        return jsonify(success=False, message='Respuesta CAPTCHA incorrecta o expirada'), 400

    fingerprint = request_fingerprint()
    recent_failures = AdminCaptchaChallenge.query.filter(
        AdminCaptchaChallenge.client_fingerprint == fingerprint,
        AdminCaptchaChallenge.login_failed.is_(True),
        AdminCaptchaChallenge.created_at >= datetime.now(timezone.utc) - LOGIN_FAILURE_WINDOW,
    ).count()
    if recent_failures >= MAX_LOGIN_FAILURES:
        return jsonify(success=False, message='Demasiados intentos; inténtalo de nuevo más tarde'), 429

    user = User.query.filter_by(email=email.strip().lower(), is_admin=True, is_active=True).first()
    if user is None or not check_password_hash(user.password_hash, password):
        challenge.login_failed = True
        challenge.client_fingerprint = fingerprint
        db.session.commit()
        return jsonify(success=False, message='Credenciales administrativas incorrectas'), 401
    AdminCaptchaChallenge.query.filter_by(client_fingerprint=fingerprint, login_failed=True).delete(synchronize_session=False)
    db.session.commit()
    login_user(user)
    session['admin_authenticated'] = True
    session.permanent = True
    return jsonify(success=True, data={
        'id': user.id,
        'email': user.email,
        'full_name': user.full_name,
        'is_admin': user.is_admin,
    }), 200


@bp.get('/auth/me')
@admin_required
def admin_me():
    return jsonify(success=True, data={
        'id': current_user.id,
        'email': current_user.email,
        'full_name': current_user.full_name,
        'is_admin': current_user.is_admin,
    }), 200


@bp.post('/auth/logout')
@admin_required
def admin_logout():
    logout_user()
    session.pop('admin_authenticated', None)
    return jsonify(success=True), 200


@bp.get('/dashboard')
@admin_required
def dashboard():
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)

    monthly_sales = db.session.query(func.coalesce(func.sum(Order.total), 0)).filter(
        Order.created_at >= month_start,
        Order.created_at < next_month,
    ).scalar()
    best_product = db.session.query(
        Product.id,
        Product.name,
        func.sum(OrderItem.quantity).label('units_sold'),
        func.sum(OrderItem.total_price).label('revenue'),
    ).join(OrderItem, OrderItem.product_id == Product.id).join(
        Order, Order.id == OrderItem.order_id,
    ).group_by(Product.id, Product.name).order_by(
        func.sum(OrderItem.quantity).desc(),
        Product.name.asc(),
    ).first()

    latest_drop = Drop.query.filter(
        Drop.starts_at <= now,
        Drop.status != 'cancelled',
    ).order_by(Drop.starts_at.desc(), Drop.id.desc()).first()
    drop_summary = None
    if latest_drop:
        drop_sales = db.session.query(func.coalesce(func.sum(OrderItem.total_price), 0)).join(
            Order, Order.id == OrderItem.order_id,
        ).filter(
            OrderItem.drop_id == latest_drop.id,
        ).scalar()
        remaining_units = db.session.query(func.coalesce(func.sum(Product.stock), 0)).filter(
            Product.drop_id == latest_drop.id,
            Product.is_active.is_(True),
        ).scalar()
        ends_at = latest_drop.ends_at
        if ends_at.tzinfo is None:
            ends_at = ends_at.replace(tzinfo=timezone.utc)
        drop_summary = {
            **serialize_drop(latest_drop),
            'sales': float(drop_sales or 0),
            'remaining_units': int(remaining_units or 0),
            'remaining_seconds': max(0, int((ends_at - now).total_seconds())),
        }

    return jsonify(success=True, data={
        'month': month_start.isoformat(),
        'monthly_sales': float(monthly_sales or 0),
        'best_selling_product': {
            'id': best_product.id,
            'name': best_product.name,
            'units_sold': int(best_product.units_sold or 0),
            'revenue': float(best_product.revenue or 0),
        } if best_product else None,
        'latest_drop': drop_summary,
    }), 200


@bp.get('/users')
@admin_required
def get_admin_users():
    users = User.query.order_by(User.id.asc()).all()
    return jsonify(success=True, data=[serialize_user(user) for user in users]), 200


@bp.post('/users')
@admin_required
def create_admin_user():
    data = request_object()
    if data is None:
        return jsonify(success=False, message='El cuerpo debe ser un objeto JSON'), 400
    full_name = data.get('full_name')
    email = data.get('email')
    password = data.get('password')
    email = normalized_email(email)
    if not isinstance(full_name, str) or not full_name.strip() or not email or len(email) > 255 or len(full_name.strip()) > 255:
        return jsonify(success=False, message='Nombre y email válido son obligatorios'), 400
    if not isinstance(password, str) or len(password) < 8:
        return jsonify(success=False, message='La contraseña debe tener al menos 8 caracteres'), 400
    if User.query.filter_by(email=email).first():
        return jsonify(success=False, message='El email ya está registrado'), 409
    if 'is_admin' in data and not isinstance(data['is_admin'], bool):
        return jsonify(success=False, message='is_admin debe ser booleano'), 400
    user = User(
        email=email,
        full_name=full_name.strip(),
        password_hash=generate_password_hash(password),
        is_admin=data.get('is_admin', False),
    )
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(success=False, message='El email ya está registrado'), 409
    return jsonify(success=True, data=serialize_user(user)), 201


def has_another_active_admin(excluded_user_id):
    return User.query.filter(
        User.is_admin.is_(True),
        User.is_active.is_(True),
        User.id != excluded_user_id,
    ).first() is not None


@bp.put('/users/<int:user_id>')
@admin_required
def update_admin_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify(success=False, message='Usuario no encontrado'), 404
    data = request_object()
    if data is None:
        return jsonify(success=False, message='El cuerpo debe ser un objeto JSON'), 400

    full_name = data.get('full_name', user.full_name)
    email = data.get('email', user.email)
    email = normalized_email(email)
    if not isinstance(full_name, str) or not full_name.strip() or not email or len(email) > 255 or len(full_name.strip()) > 255:
        return jsonify(success=False, message='Nombre y email válido son obligatorios'), 400
    duplicate = User.query.filter(User.email == email, User.id != user.id).first()
    if duplicate:
        return jsonify(success=False, message='El email ya está registrado'), 409
    if 'password' in data:
        password = data['password']
        if not isinstance(password, str) or len(password) < 8:
            return jsonify(success=False, message='La contraseña debe tener al menos 8 caracteres'), 400
        user.password_hash = generate_password_hash(password)

    next_is_admin = data.get('is_admin', user.is_admin)
    next_is_active = data.get('is_active', user.is_active)
    if not isinstance(next_is_admin, bool) or not isinstance(next_is_active, bool):
        return jsonify(success=False, message='Los estados de cuenta deben ser booleanos'), 400
    if user.is_admin and user.is_active and not (next_is_admin and next_is_active):
        if user.id == current_user.id or not has_another_active_admin(user.id):
            return jsonify(success=False, message='No puedes desactivar o degradar al último administrador'), 409

    user.full_name = full_name.strip()
    user.email = email
    user.is_admin = next_is_admin
    user.is_active = next_is_active
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(success=False, message='No se pudo actualizar el usuario por un email duplicado'), 409
    return jsonify(success=True, data=serialize_user(user)), 200


@bp.delete('/users/<int:user_id>')
@admin_required
def deactivate_admin_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify(success=False, message='Usuario no encontrado'), 404
    if user.is_admin and user.is_active and (user.id == current_user.id or not has_another_active_admin(user.id)):
        return jsonify(success=False, message='No puedes desactivar al último administrador'), 409
    user.is_active = False
    db.session.commit()
    return jsonify(success=True, data=serialize_user(user)), 200


@bp.get('/products')
@admin_required
def get_admin_products():
    products = Product.query.order_by(Product.id.desc()).all()
    return jsonify(success=True, data=[serialize_product(product) for product in products]), 200


def product_values(data, product=None):
    name = data.get('name', product.name if product else None)
    category_id = data.get('category_id', product.category_id if product else None)
    price_value = data.get('price', product.price if product else None)
    stock = data.get('stock', product.stock if product else 0)
    description = data.get('description', product.description if product else None)
    image_url = data.get('image_url', product.image_url if product else None)
    drop_id = data.get('drop_id', product.drop_id if product else None)
    is_active = data.get('is_active', product.is_active if product else True)

    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 255:
        return None, 'El nombre del producto es obligatorio'
    if not isinstance(category_id, int) or isinstance(category_id, bool) or db.session.get(Category, category_id) is None:
        return None, 'Selecciona una categoría válida'
    try:
        price = Decimal(str(price_value))
        valid_price = (
            price.is_finite()
            and price > 0
            and price <= Decimal('99999999.99')
            and price == price.quantize(Decimal('0.01'))
        )
    except (InvalidOperation, ValueError):
        return None, 'El precio no es válido'
    if not valid_price:
        return None, 'El precio debe tener hasta dos decimales y estar dentro del rango permitido'
    if not isinstance(stock, int) or isinstance(stock, bool) or stock < 0 or stock > 2147483647:
        return None, 'El inventario debe ser un entero no negativo'
    if description is not None and not isinstance(description, str):
        return None, 'La descripción debe ser texto'
    if image_url is not None and not isinstance(image_url, str):
        return None, 'La URL de imagen debe ser texto'
    if image_url and len(image_url) > 500:
        return None, 'La URL de imagen supera el límite permitido'
    if drop_id is not None:
        if not isinstance(drop_id, int) or isinstance(drop_id, bool) or db.session.get(Drop, drop_id) is None:
            return None, 'Selecciona un drop válido'
    if not isinstance(is_active, bool):
        return None, 'El estado del producto debe ser booleano'
    return {
        'name': name.strip(),
        'category_id': category_id,
        'price': price,
        'stock': stock,
        'description': description.strip() if description else None,
        'image_url': image_url.strip() if image_url else None,
        'drop_id': drop_id,
        'is_active': is_active,
    }, None


@bp.post('/products')
@admin_required
def create_admin_product():
    payload = request_object()
    if payload is None:
        return jsonify(success=False, message='El cuerpo debe ser un objeto JSON'), 400
    data, error = product_values(payload)
    if error:
        return jsonify(success=False, message=error), 400
    product = Product(**data)
    db.session.add(product)
    db.session.commit()
    return jsonify(success=True, data=serialize_product(product)), 201


@bp.put('/products/<int:product_id>')
@admin_required
def update_admin_product(product_id):
    product = db.session.get(Product, product_id)
    if product is None:
        return jsonify(success=False, message='Producto no encontrado'), 404
    payload = request_object()
    if payload is None:
        return jsonify(success=False, message='El cuerpo debe ser un objeto JSON'), 400
    data, error = product_values(payload, product)
    if error:
        return jsonify(success=False, message=error), 400
    for field, value in data.items():
        setattr(product, field, value)
    db.session.commit()
    return jsonify(success=True, data=serialize_product(product)), 200


@bp.delete('/products/<int:product_id>')
@admin_required
def deactivate_admin_product(product_id):
    product = db.session.get(Product, product_id)
    if product is None:
        return jsonify(success=False, message='Producto no encontrado'), 404
    product.is_active = False
    db.session.commit()
    return jsonify(success=True, data=serialize_product(product)), 200


def parse_datetime(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def drop_values(data, drop=None):
    name = data.get('name', drop.name if drop else None)
    starts_at = parse_datetime(data.get('starts_at', drop.starts_at.isoformat() if drop else None))
    ends_at = parse_datetime(data.get('ends_at', drop.ends_at.isoformat() if drop else None))
    description = data.get('description', drop.description if drop else None)
    status = data.get('status', drop.status if drop else 'scheduled')
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 255:
        return None, 'El nombre del drop es obligatorio'
    if starts_at is None or ends_at is None or starts_at >= ends_at:
        return None, 'El drop requiere fechas válidas y la fecha final debe ser posterior a la inicial'
    if description is not None and not isinstance(description, str):
        return None, 'La descripción debe ser texto'
    if not isinstance(status, str) or status not in ALLOWED_DROP_STATUSES:
        return None, 'El estado del drop no es válido'
    return {
        'name': name.strip(),
        'starts_at': starts_at,
        'ends_at': ends_at,
        'description': description.strip() if description else None,
        'status': status,
    }, None


@bp.get('/drops')
@admin_required
def get_admin_drops():
    drops = Drop.query.order_by(Drop.starts_at.desc(), Drop.id.desc()).all()
    return jsonify(success=True, data=[serialize_drop(drop) for drop in drops]), 200


@bp.post('/drops')
@admin_required
def create_admin_drop():
    payload = request_object()
    if payload is None:
        return jsonify(success=False, message='El cuerpo debe ser un objeto JSON'), 400
    data, error = drop_values(payload)
    if error:
        return jsonify(success=False, message=error), 400
    drop = Drop(**data)
    db.session.add(drop)
    db.session.commit()
    return jsonify(success=True, data=serialize_drop(drop)), 201


@bp.put('/drops/<int:drop_id>')
@admin_required
def update_admin_drop(drop_id):
    drop = db.session.get(Drop, drop_id)
    if drop is None:
        return jsonify(success=False, message='Drop no encontrado'), 404
    payload = request_object()
    if payload is None:
        return jsonify(success=False, message='El cuerpo debe ser un objeto JSON'), 400
    data, error = drop_values(payload, drop)
    if error:
        return jsonify(success=False, message=error), 400
    for field, value in data.items():
        setattr(drop, field, value)
    db.session.commit()
    return jsonify(success=True, data=serialize_drop(drop)), 200


@bp.delete('/drops/<int:drop_id>')
@admin_required
def delete_admin_drop(drop_id):
    drop = db.session.get(Drop, drop_id)
    if drop is None:
        return jsonify(success=False, message='Drop no encontrado'), 404
    if Product.query.filter_by(drop_id=drop.id).first():
        return jsonify(success=False, message='Quita primero los productos asociados para conservar su historial'), 409
    if OrderItem.query.filter_by(drop_id=drop.id).first():
        return jsonify(success=False, message='No se puede eliminar un drop con ventas históricas asociadas'), 409
    db.session.delete(drop)
    db.session.commit()
    return jsonify(success=True), 200
