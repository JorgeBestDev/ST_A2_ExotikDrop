from flask import Blueprint, jsonify

from app.models.drops import Drop

bp = Blueprint('drops', __name__, url_prefix='/api/drops')


def serialize_drop(drop):
    return {
        'id': drop.id,
        'name': drop.name,
        'description': drop.description,
        'starts_at': drop.starts_at.isoformat() if drop.starts_at else None,
        'ends_at': drop.ends_at.isoformat() if drop.ends_at else None,
        'status': drop.status,
        'created_at': drop.created_at.isoformat() if drop.created_at else None,
    }


@bp.route('', methods=['GET'])
@bp.route('/', methods=['GET'])
def get_drops():
    drops = Drop.query.order_by(Drop.id.asc()).all()
    return jsonify({
        'success': True,
        'data': [serialize_drop(drop) for drop in drops],
        'count': len(drops)
    }), 200


@bp.route('/<int:drop_id>', methods=['GET'])
def get_drop(drop_id):
    drop = Drop.query.get(drop_id)

    if drop is None:
        return jsonify({
            'success': False,
            'message': 'Drop no encontrado'
        }), 404

    return jsonify({
        'success': True,
        'data': serialize_drop(drop)
    }), 200
