from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from app.models.orders import Order

bp = Blueprint('orders', __name__, url_prefix='/api/orders')


def serialize_order(order):
    return {
        'id': order.id,
        'user_id': order.user_id,
        'total': float(order.total) if order.total is not None else None,
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
            'quantity': item.quantity,
            'unit_price': float(item.unit_price),
            'total_price': float(item.total_price),
        } for item in order.items],
        'payment': {'method': order.payment.method, 'status': order.payment.status} if order.payment else None,
    }


@bp.route('', methods=['GET'])
@bp.route('/', methods=['GET'])
@login_required
def get_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.id.desc()).all()
    return jsonify({
        'success': True,
        'data': [serialize_order(order) for order in orders],
        'count': len(orders)
    }), 200


@bp.route('/<int:order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()

    if order is None:
        return jsonify({
            'success': False,
            'message': 'Pedido no encontrado'
        }), 404

    return jsonify({
        'success': True,
        'data': serialize_order(order)
    }), 200
