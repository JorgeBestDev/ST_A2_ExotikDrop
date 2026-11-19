from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models.products import Product
from app.services.inventory import available_stock, reserved_quantities

bp = Blueprint('products', __name__, url_prefix='/api/products')


#convierte un objeto Product en un diccionario leible para JSON
def serialize_product(product, reserved=None):
    return {
        'id': product.id,
        'category_id': product.category_id,
        'drop_id': product.drop_id,
        'category': product.category.name if product.category else None,
        'name': product.name,
        'description': product.description,
        'price': f'{product.price:.2f}',
        'stock': available_stock(product, reserved=reserved),
        'image_url': product.image_url,
        'is_active': product.is_active,
        'created_at': product.created_at.isoformat() if product.created_at else None
    }

#get de productos
@bp.route('', methods=['GET'])
@bp.route('/', methods=['GET'])
def get_products():
    products = Product.query.filter_by(is_active=True).order_by(Product.id.asc()).all()
    reserved = reserved_quantities(product.id for product in products)
    return jsonify({
        'success': True,
        'data': [serialize_product(product, reserved.get(product.id, 0)) for product in products],
        'count': len(products)
    }), 200
    
@bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.filter_by(id=product_id, is_active=True).first()

    if product is None:
        return jsonify({
            'success': False,
            'message': 'Producto no encontrado'
        }), 404

    reserved = reserved_quantities([product.id]).get(product.id, 0)
    return jsonify({
        'success': True,
        'data': serialize_product(product, reserved)
    }), 200