from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from app import db
from .event import eventData
from sqlalchemy import DateTime, func
from .user import User
from .item import Item

class WithdrawHistory(db.Model, SerializerMixin):
    table = "withdraw_history"
    WIthdrawID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey("user.UserId"), nullable=False)
    User = db.relationship("User", back_populates = "withdraw_history")
    ItemID = db.Column(db.Integer, db.ForeignKey("Item.itemId"), nullable=False)
    Item = db.relationship("Item", back_populates = "withdraw_history")
    Quantity = db.Column(db.Integer)
    DateTime = db.Column(DateTime, nullable=False, default=func.utcnow())
    
    def __init__(self, quantity):
        self.Quantity = quantity
