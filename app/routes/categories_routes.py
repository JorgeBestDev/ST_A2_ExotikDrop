from flask import Blueprint, jsonify

from app.models.categories import Category

bp = Blueprint('categories', __name__, url_prefix='/api/categories')


def serialize_category(category):
    return {
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'image_url': next(
            (product.image_url for product in category.products if product.image_url),
            None,
        ),
    }


@bp.route('', methods=['GET'])
@bp.route('/', methods=['GET'])
def get_categories():
    categories = Category.query.order_by(Category.id.asc()).all()
    return jsonify({
        'success': True,
        'data': [serialize_category(category) for category in categories],
        'count': len(categories)
    }), 200


@bp.route('/<int:category_id>', methods=['GET'])
def get_category(category_id):
    category = Category.query.get(category_id)

    if category is None:
        return jsonify({
            'success': False,
            'message': 'Categoría no encontrada'
        }), 404

    return jsonify({
        'success': True,
        'data': serialize_category(category)
    }), 200
