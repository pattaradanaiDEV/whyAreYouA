from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from app import db
from sqlalchemy import DateTime, func
from datetime import datetime
from dateutil import tz
#from tzlocal import get_localzone

def test():
        utc_time = datetime.now()    
        to_zone = tz.tzlocal()
        return utc_time.astimezone(to_zone)

class WithdrawHistory(db.Model, SerializerMixin):
    __tablename__ = "withdrawHistory"

    withdrawID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey("user.UserID", ondelete='SET NULL'), nullable=True)
    itemID = db.Column(db.Integer, db.ForeignKey("item.itemID"), nullable=False)
    Quantity = db.Column(db.Integer)
    DateTime = db.Column(db.DateTime(timezone=True), default=lambda: test())

    user = db.relationship("User", back_populates="withdraw_history")
    items = db.relationship("Item", back_populates="withdraw_history")

    serialize_only = ("withdrawID", "Quantity", "DateTime", "items.itemID","items.itemName","UserID")

    def __init__(self, user_id, item_id, quantity):
        self.UserID = user_id
        self.itemID = item_id
        self.Quantity = quantity