from app import db
from datetime import datetime, timedelta, timezone
from sqlalchemy_serializer import SerializerMixin
class Notification(db.Model, SerializerMixin):
    __tablename__ = "notification"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.UserID"), nullable=True)
    type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone(timedelta(hours=7))))
    expire_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone(timedelta(hours=7))) + timedelta(days=7))
    is_read = db.Column(db.Boolean, default=False)

    user = db.relationship("User", back_populates="notifications")
    serialize_only = ("id","user_id","type","message","created_at","expire_at","is_read")

    def __init__(self, user_id, ntype, message):
        self.user_id = user_id
        self.type = ntype
        self.message = message
        tz = timezone(timedelta(hours=7))
        self.created_at = datetime.now(tz)
        self.expire_at = datetime.now(tz) + timedelta(days=7)
