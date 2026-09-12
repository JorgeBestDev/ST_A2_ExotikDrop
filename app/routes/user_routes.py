from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models.users import User

bp = Blueprint('users', __name__, url_prefix='/api/users')

#convierte un objeto User en un diccionario leible para JSON
def serialize_user(user):
    return {
        'id': user.id,
        'email': user.email,
        'full_name': user.full_name,
        'is_admin': user.is_admin,
        'created_at': user.created_at.isoformat() if user.created_at else None
    }


@bp.route('', methods=['GET'])
@bp.route('/', methods=['GET'])
def get_users():
    users = User.query.order_by(User.id.asc()).all()
    return jsonify({
        'success': True,
        'data': [serialize_user(user) for user in users],
        'count': len(users)
    }), 200


@bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)

    if user is None:
        return jsonify({
            'success': False,
            'message': 'Usuario no encontrado'
        }), 404

    return jsonify({
        'success': True,
        'data': serialize_user(user)
    }), 200


@bp.route('', methods=['POST'])
@bp.route('/', methods=['POST'])
def create_user():
    data = request.get_json(silent=True) or {}

    email = (data.get('email') or '').strip()
    password = data.get('password')
    full_name = (data.get('full_name') or '').strip()
    is_admin = bool(data.get('is_admin', False))

    if not email or not password or not full_name:
        return jsonify({
            'success': False,
            'message': 'Email, password y full_name son obligatorios'
        }), 400

    if User.query.filter_by(email=email).first():
        return jsonify({
            'success': False,
            'message': 'El email ya está registrado'
        }), 409

    user = User(
        email=email,
        password_hash=generate_password_hash(password),
        full_name=full_name,
        is_admin=is_admin
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Usuario creado correctamente',
        'data': serialize_user(user)
    }), 201


@bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json(silent=True) or {}
    user = User.query.get(user_id)

    if user is None:
        return jsonify({
            'success': False,
            'message': 'Usuario no encontrado'
        }), 404

    if 'email' in data and data.get('email'):
        email = data['email'].strip()
        if email != user.email and User.query.filter_by(email=email).first():
            return jsonify({
                'success': False,
                'message': 'El email ya está registrado'
            }), 409
        user.email = email

    if 'full_name' in data and data.get('full_name'):
        user.full_name = data['full_name'].strip()

    if 'is_admin' in data:
        user.is_admin = bool(data.get('is_admin'))

    if 'password' in data and data.get('password'):
        user.password_hash = generate_password_hash(data['password'])

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Usuario actualizado correctamente',
        'data': serialize_user(user)
    }), 200


@bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)

    if user is None:
        return jsonify({
            'success': False,
            'message': 'Usuario no encontrado'
        }), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Usuario eliminado correctamente'
    }), 200
