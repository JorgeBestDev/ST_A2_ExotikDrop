from datetime import datetime, timezone

from app.extensions import db


class AdminCaptchaChallenge(db.Model):
    __tablename__ = 'admin_captcha_challenges'

    id = db.Column(db.String(36), primary_key=True)
    answer_hash = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    consumed = db.Column(db.Boolean, nullable=False, default=False)
    client_fingerprint = db.Column(db.String(64), nullable=True)
    login_failed = db.Column(db.Boolean, nullable=False, default=False)
