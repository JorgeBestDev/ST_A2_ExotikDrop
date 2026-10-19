from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from app.models.carts import Cart

bp = Blueprint('carts', __name__, url_prefix='/api/carts')


def serialize_cart(cart):
    return {
        'id': cart.id,
        'user_id': cart.user_id,
        'created_at': cart.created_at.isoformat() if cart.created_at else None,
    }


@bp.route('', methods=['GET'])
@bp.route('/', methods=['GET'])
@login_required
def get_carts():
    carts = Cart.query.filter_by(user_id=current_user.id).order_by(Cart.id.asc()).all()
    return jsonify({
        'success': True,
        'data': [serialize_cart(cart) for cart in carts],
        'count': len(carts)
    }), 200


@bp.route('/<int:cart_id>', methods=['GET'])
@login_required
def get_cart(cart_id):
    cart = Cart.query.filter_by(id=cart_id, user_id=current_user.id).first()

    if cart is None:
        return jsonify({
            'success': False,
            'message': 'Carrito no encontrado'
        }), 404

    return jsonify({
        'success': True,
        'data': serialize_cart(cart)
    }), 200
