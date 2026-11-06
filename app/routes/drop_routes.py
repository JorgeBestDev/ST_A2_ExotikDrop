from datetime import datetime, timezone

from flask import Blueprint, jsonify
from sqlalchemy import and_, or_

from app.extensions import db
from app.models.drops import Drop
from app.models.products import Product
from app.routes.product_routes import serialize_product

bp = Blueprint('drops', __name__, url_prefix='/api/drops')


def serialize_datetime(value):
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat()


def serialize_drop(drop):
    return {
        'id': drop.id,
        'name': drop.name,
        'description': drop.description,
        'starts_at': serialize_datetime(drop.starts_at),
        'ends_at': serialize_datetime(drop.ends_at),
        'status': drop.status,
        'created_at': serialize_datetime(drop.created_at),
    }


@bp.route('', methods=['GET'])
@bp.route('/', methods=['GET'])
def get_drops():
    drops = Drop.query.order_by(Drop.id.asc()).all()
    return jsonify({
        'success': True,
        'data': [serialize_drop(drop) for drop in drops],
        'count': len(drops)
    }), 200


@bp.route('/<int:drop_id>', methods=['GET'])
def get_drop(drop_id):
    drop = Drop.query.get(drop_id)

    if drop is None:
        return jsonify({
            'success': False,
            'message': 'Drop no encontrado'
        }), 404

    return jsonify({
        'success': True,
        'data': serialize_drop(drop)
    }), 200


@bp.route('/featured', methods=['GET'])
def get_featured_drop():
    now = datetime.now(timezone.utc)
    drop = Drop.query.filter(
        Drop.status == 'active',
        Drop.starts_at <= now,
        Drop.ends_at > now,
    ).order_by(Drop.starts_at.desc(), Drop.id.desc()).first()
    is_active = drop is not None

    if drop is None:
        drop = Drop.query.filter(
            or_(
                Drop.status == 'ended',
                and_(Drop.status == 'active', Drop.ends_at <= now),
            )
        ).order_by(Drop.ends_at.desc(), Drop.id.desc()).first()

    if drop is None:
        return jsonify({'success': True, 'data': None}), 200

    products = Product.query.filter_by(
        drop_id=drop.id,
        is_active=True,
    ).order_by(Product.id.asc()).all()

    return jsonify({
        'success': True,
        'data': {
            'status': 'active' if is_active else 'ended',
            'drop': serialize_drop(drop),
            'products': [serialize_product(product) for product in products],
        },
    }), 200
