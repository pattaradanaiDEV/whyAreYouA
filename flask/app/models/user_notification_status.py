from app import db
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy import PrimaryKeyConstraint

class UserNotificationStatus(db.Model, SerializerMixin):
    __tablename__ = 'user_notification_status'

    user_id = db.Column(db.Integer, db.ForeignKey('user.UserID'), nullable=False)
    notification_id = db.Column(db.Integer, db.ForeignKey('notification.id'), nullable=False)
    
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship("User", back_populates="notification_statuses")
    notification = db.relationship("Notification", back_populates="user_statuses")

    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'notification_id'),
    )

    def __init__(self, user_id, notification_id):
        self.user_id = user_id
        self.notification_id = notification_id
