from app import db
from datetime import datetime, timedelta

class Notification(db.Model):
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

    # relationship to User (actor)
    user = db.relationship("User", backref="triggered_notifications", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expire_at": self.expire_at.isoformat() if self.expire_at else None,
            "is_read": self.is_read
        }

    @staticmethod
    def create(user_id, ntype, message):
        from app import db
        from datetime import datetime, timedelta
        noti = Notification(
            user_id=user_id,
            type=ntype,
            message=message,
            created_at=datetime.utcnow(),
            expire_at=datetime.utcnow() + timedelta(days=7),
            is_read=False
        )
        db.session.add(noti)
        db.session.commit()
        return noti
