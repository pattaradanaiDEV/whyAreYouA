from app import db
from datetime import datetime, timedelta
from sqlalchemy_serializer import SerializerMixin
class Notification(db.Model,SerializerMixin):
    __tablename__ = "notification"

    id = db.Column(db.Integer, primary_key=True)
    # user_id here is the actor who triggered notification (nullable)
    user_id = db.Column(db.Integer, db.ForeignKey("user.UserID"), nullable=True)
    # target_admin_only: if True, only main admins see it.
    type = db.Column(db.String(50), nullable=False)   # e.g. withdraw, signup, low_stock
    message = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expire_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))
    is_read = db.Column(db.Boolean, default=False)
    user = db.relationship("User",  back_populates="notifications")
    serialize_only = ("id","user_id","type","message","created_at","expire_at","is_read")
    def __init__(self,user_id,ntype,message):
        self.user_id = user_id
        self.type = ntype
        self.message=message
        self.created_at=datetime.utcnow()
        self.expire_at=datetime.utcnow() + timedelta(days=7)
        