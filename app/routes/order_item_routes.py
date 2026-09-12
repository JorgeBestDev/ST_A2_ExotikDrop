from flask import Blueprint, jsonify

from app.models.order_items import OrderItem

bp = Blueprint('order_items', __name__, url_prefix='/api/order-items')


def serialize_order_item(order_item):
    return {
        'id': order_item.id,
        'order_id': order_item.order_id,
        'product_id': order_item.product_id,
        'quantity': order_item.quantity,
        'unit_price': float(order_item.unit_price) if order_item.unit_price is not None else None,
        'total_price': float(order_item.total_price) if order_item.total_price is not None else None,
    }


@bp.route('', methods=['GET'])
@bp.route('/', methods=['GET'])
def get_order_items():
    order_items = OrderItem.query.order_by(OrderItem.id.asc()).all()
    return jsonify({
        'success': True,
        'data': [serialize_order_item(item) for item in order_items],
        'count': len(order_items)
    }), 200


@bp.route('/<int:order_item_id>', methods=['GET'])
def get_order_item(order_item_id):
    order_item = OrderItem.query.get(order_item_id)

    if order_item is None:
        return jsonify({
            'success': False,
            'message': 'Detalle de pedido no encontrado'
        }), 404

    return jsonify({
        'success': True,
        'data': serialize_order_item(order_item)
    }), 200
