from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from app.extensions import db
from app.models.carts import Cart
from app.models.cart_items import CartItem

bp = Blueprint('cart_items', __name__, url_prefix='/api/cart-items')


def serialize_cart_item(cart_item):
    return {
        'id': cart_item.id,
        'cart_id': cart_item.cart_id,
        'product_id': cart_item.product_id,
        'quantity': cart_item.quantity,
        'added_at': cart_item.added_at.isoformat() if cart_item.added_at else None,
    }


@bp.route('', methods=['GET'])
@bp.route('/', methods=['GET'])
@login_required
def get_cart_items():
    cart_ids = db.session.query(Cart.id).filter_by(user_id=current_user.id)
    cart_items = CartItem.query.filter(CartItem.cart_id.in_(cart_ids)).order_by(CartItem.id.asc()).all()
    return jsonify({
        'success': True,
        'data': [serialize_cart_item(item) for item in cart_items],
        'count': len(cart_items)
    }), 200


@bp.route('/<int:cart_item_id>', methods=['GET'])
@login_required
def get_cart_item(cart_item_id):
    cart_item = CartItem.query.join(Cart).filter(
        CartItem.id == cart_item_id,
        Cart.user_id == current_user.id,
    ).first()

    if cart_item is None:
        return jsonify({
            'success': False,
            'message': 'Item del carrito no encontrado'
        }), 404

    return jsonify({
        'success': True,
        'data': serialize_cart_item(cart_item)
    }), 200
