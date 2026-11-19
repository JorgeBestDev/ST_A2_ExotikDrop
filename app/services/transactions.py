from functools import wraps

from app.extensions import db


def rollback_on_error(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        try:
            result = view(*args, **kwargs)
            status = result[1] if isinstance(result, tuple) and len(result) > 1 else getattr(result, 'status_code', 200)
            if status >= 400:
                db.session.rollback()
            elif db.session().in_transaction():
                db.session.commit()
            return result
        except Exception:
            db.session.rollback()
            raise

    return wrapped
