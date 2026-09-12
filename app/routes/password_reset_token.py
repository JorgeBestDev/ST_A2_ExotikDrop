from flask import Blueprint, jsonify

from app.models.password_reset_tokens import PasswordResetToken

bp = Blueprint('password_reset_tokens', __name__, url_prefix='/api/password-reset-tokens')


def serialize_password_reset_token(token_record):
    return {
        'id': token_record.id,
        'user_id': token_record.user_id,
        'token': token_record.token,
        'created_at': token_record.created_at.isoformat() if token_record.created_at else None,
    }


@bp.route('', methods=['GET'])
@bp.route('/', methods=['GET'])
def get_password_reset_tokens():
    tokens = PasswordResetToken.query.order_by(PasswordResetToken.id.asc()).all()
    return jsonify({
        'success': True,
        'data': [serialize_password_reset_token(token_record) for token_record in tokens],
        'count': len(tokens)
    }), 200


@bp.route('/<int:token_id>', methods=['GET'])
def get_password_reset_token(token_id):
    token_record = PasswordResetToken.query.get(token_id)

    if token_record is None:
        return jsonify({
            'success': False,
            'message': 'Token no encontrado'
        }), 404

    return jsonify({
        'success': True,
        'data': serialize_password_reset_token(token_record)
    }), 200
