from flask import Blueprint, jsonify

from app.models.orders import Order

bp = Blueprint('orders', __name__, url_prefix='/api/orders')


def serialize_order(order):
    return {
        'id': order.id,
        'user_id': order.user_id,
        'total': float(order.total) if order.total is not None else None,
        'status': order.status,
        'created_at': order.created_at.isoformat() if order.created_at else None,
    }


@bp.route('', methods=['GET'])
@bp.route('/', methods=['GET'])
def get_orders():
    orders = Order.query.order_by(Order.id.asc()).all()
    return jsonify({
        'success': True,
        'data': [serialize_order(order) for order in orders],
        'count': len(orders)
    }), 200


@bp.route('/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = Order.query.get(order_id)

    if order is None:
        return jsonify({
            'success': False,
            'message': 'Pedido no encontrado'
        }), 404

    return jsonify({
        'success': True,
        'data': serialize_order(order)
    }), 200
