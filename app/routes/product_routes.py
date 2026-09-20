from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models.products import Product

bp = Blueprint('products', __name__, url_prefix='/api/products')


#convierte un objeto Product en un diccionario leible para JSON
def serialize_product(product):
    return {
        'id': product.id,
        'category_id': product.category_id,
        'category': product.category.name if product.category else None,
        'name': product.name,
        'description': product.description,
        'price': f'{product.price:.2f}',
        'stock': product.stock,
        'image_url': product.image_url,
        'is_active': product.is_active,
        'created_at': product.created_at.isoformat() if product.created_at else None
    }

#get de productos
@bp.route('', methods=['GET'])
@bp.route('/', methods=['GET'])
def get_products():
    products = Product.query.filter_by(is_active=True).order_by(Product.id.asc()).all()
    return jsonify({
        'success': True,
        'data': [serialize_product(product) for product in products],
        'count': len(products)
    }), 200
    
@bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)

    if product is None:
        return jsonify({
            'success': False,
            'message': 'Producto no encontrado'
        }), 404

    return jsonify({
        'success': True,
        'data': serialize_product(product)
    }), 200