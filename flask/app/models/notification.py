from app import db
from datetime import datetime, timedelta, timezone
from sqlalchemy_serializer import SerializerMixin

class Notification(db.Model, SerializerMixin):
    __tablename__ = "notification"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.UserID", ondelete='SET NULL'), nullable=True)

    ntype = db.Column(db.String(50), nullable=False) 
    message = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expire_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc) + timedelta(days=7))
   
    actor = db.relationship("User") 
    user_statuses = db.relationship("UserNotificationStatus", back_populates="notification", cascade="all, delete-orphan", passive_deletes=True)
    serialize_only = ("id", "user_id", "ntype", "message", "created_at", "expire_at", "actor.Fname")

    def __init__(self, ntype, message, user_id=None):
        self.ntype = ntype
        self.message = message
        self.user_id = user_id