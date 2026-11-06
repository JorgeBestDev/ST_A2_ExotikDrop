from flask import Blueprint, jsonify, request, session
from flask_login import current_user, login_required
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
        'is_active': user.is_active,
        'created_at': user.created_at.isoformat() if user.created_at else None
    }


def has_admin_access():
    return current_user.is_admin and session.get('admin_authenticated')


@bp.route('', methods=['GET'])
@bp.route('/', methods=['GET'])
@login_required
def get_users():
    if not has_admin_access():
        return jsonify(success=False, message='No tienes permiso para consultar usuarios'), 403
    users = User.query.order_by(User.id.asc()).all()
    return jsonify({
        'success': True,
        'data': [serialize_user(user) for user in users],
        'count': len(users)
    }), 200


@bp.route('/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    if current_user.id != user_id and not has_admin_access():
        return jsonify(success=False, message='No tienes permiso para consultar este usuario'), 403
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
        is_admin=False,
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Usuario creado correctamente',
        'data': serialize_user(user)
    }), 201


@bp.route('/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    if current_user.id != user_id and not has_admin_access():
        return jsonify(success=False, message='No tienes permiso para actualizar este usuario'), 403
    data = request.get_json(silent=True) or {}
    user = User.query.get(user_id)

    if user is None:
        return jsonify({
            'success': False,
            'message': 'Usuario no encontrado'
        }), 404

    if 'is_admin' in data and not has_admin_access():
        return jsonify(success=False, message='No tienes permiso para cambiar privilegios'), 403
    if 'password' in data and data.get('password') and not has_admin_access():
        return jsonify(success=False, message='Usa la ruta de cambio de contraseña de la cuenta'), 400

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

    if 'is_admin' in data and has_admin_access():
        next_is_admin = data.get('is_admin')
        if not isinstance(next_is_admin, bool):
            return jsonify(success=False, message='is_admin debe ser booleano'), 400
        if user.is_admin and user.is_active and not next_is_admin:
            other_active_admin = User.query.filter(
                User.is_admin.is_(True),
                User.is_active.is_(True),
                User.id != user.id,
            ).first()
            if user.id == current_user.id or other_active_admin is None:
                return jsonify(success=False, message='No puedes degradar al último administrador'), 409
        user.is_admin = next_is_admin

    if 'password' in data and data.get('password'):
        user.password_hash = generate_password_hash(data['password'])

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Usuario actualizado correctamente',
        'data': serialize_user(user)
    }), 200


@bp.route('/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if not has_admin_access():
        return jsonify(success=False, message='No tienes permiso para eliminar usuarios'), 403
    user = User.query.get(user_id)

    if user is None:
        return jsonify({
            'success': False,
            'message': 'Usuario no encontrado'
        }), 404

    if user.is_admin and user.is_active:
        other_active_admin = User.query.filter(
            User.is_admin.is_(True),
            User.is_active.is_(True),
            User.id != user.id,
        ).first()
        if user.id == current_user.id or other_active_admin is None:
            return jsonify(success=False, message='No puedes desactivar al último administrador'), 409
    user.is_active = False
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Usuario desactivado correctamente'
    }), 200
