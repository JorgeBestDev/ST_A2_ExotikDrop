from flask import Blueprint, render_template

bp = Blueprint('main', __name__)


def register_routes(app):
    from app.routes import (
        user_routes,
        product_routes,
        payment_routes,
        password_reset_token,
        order_routes,
        order_item_routes,
        drop_routes,
        categories_routes,
        carts_routes,
        cart_item,
    )

    app.register_blueprint(user_routes.bp)
    app.register_blueprint(product_routes.bp)
    app.register_blueprint(payment_routes.bp)
    app.register_blueprint(password_reset_token.bp)
    app.register_blueprint(order_routes.bp)
    app.register_blueprint(order_item_routes.bp)
    app.register_blueprint(drop_routes.bp)
    app.register_blueprint(categories_routes.bp)
    app.register_blueprint(carts_routes.bp)
    app.register_blueprint(cart_item.bp)

    return app