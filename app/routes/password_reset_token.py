from flask import Blueprint, jsonify
from flask_login import current_user, login_required

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
@login_required
def get_password_reset_tokens():
    tokens = PasswordResetToken.query.filter_by(user_id=current_user.id).order_by(PasswordResetToken.id.asc()).all()
    return jsonify({
        'success': True,
        'data': [serialize_password_reset_token(token_record) for token_record in tokens],
        'count': len(tokens)
    }), 200


@bp.route('/<int:token_id>', methods=['GET'])
@login_required
def get_password_reset_token(token_id):
    token_record = PasswordResetToken.query.filter_by(id=token_id, user_id=current_user.id).first()

    if token_record is None:
        return jsonify({
            'success': False,
            'message': 'Token no encontrado'
        }), 404

    return jsonify({
        'success': True,
        'data': serialize_password_reset_token(token_record)
    }), 200
