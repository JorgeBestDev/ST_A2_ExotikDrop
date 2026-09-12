from flask import Blueprint, jsonify

from app.models.payments import Payment

bp = Blueprint('payments', __name__, url_prefix='/api/payments')


def serialize_payment(payment):
    return {
        'id': payment.id,
        'order_id': payment.order_id,
        'method': payment.method,
        'amount': float(payment.amount) if payment.amount is not None else None,
        'status': payment.status,
        'created_at': payment.created_at.isoformat() if payment.created_at else None,
    }


@bp.route('', methods=['GET'])
@bp.route('/', methods=['GET'])
def get_payments():
    payments = Payment.query.order_by(Payment.id.asc()).all()
    return jsonify({
        'success': True,
        'data': [serialize_payment(payment) for payment in payments],
        'count': len(payments)
    }), 200


@bp.route('/<int:payment_id>', methods=['GET'])
def get_payment(payment_id):
    payment = Payment.query.get(payment_id)

    if payment is None:
        return jsonify({
            'success': False,
            'message': 'Pago no encontrado'
        }), 404

    return jsonify({
        'success': True,
        'data': serialize_payment(payment)
    }), 200
