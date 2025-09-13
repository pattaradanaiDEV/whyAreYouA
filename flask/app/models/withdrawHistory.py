from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from app import db
from .event import eventData
from sqlalchemy import DateTime, func
class WithdrawHistory(db.Model, SerializerMixin):
    table = "withdrawHistory"
    withdrawID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey("user.UserID"), nullable=False)
    item = db.Column(db.Integer, db.ForeignKey("Item.itemID"), nullable=False)
    Quantity = db.Column(db.Integer)
    DateTime = db.Column(DateTime, nullable=False, default=func.utcnow())
    
    user = db.relationship("User", back_populates = "withdraw_history")
    items = db.relationship("Item", back_populates = "withdraw_history")
    serialize_only = ("withdrawID", "Quantity", "DateTime", "item")
    def __init__(self, quantity):
        self.Quantity = quantity
