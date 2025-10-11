import segno
import base64
from io import BytesIO
from app import db
from sqlalchemy_serializer import SerializerMixin
class Item(db.Model,SerializerMixin):
    __tablename__ = "item"
    itemID = db.Column(db.Integer, primary_key=True)
    cateID = db.Column(db.Integer, db.ForeignKey("category.cateID"), default = 1)
    itemName = db.Column(db.String(255))
    itemAmount = db.Column(db.Integer)
    itemPicture = db.Column(db.String(255))
    itemMin = db.Column(db.Integer)
    itemDesc = db.Column(db.String(500))

    category = db.relationship("Category", back_populates="items")
    cart_items = db.relationship("CartItem", back_populates="item" ,  cascade="all, delete-orphan")
    serialize_only = (
        "itemID",
        "itemName",
        "itemAmount",
        "itemPicture",
        "itemMin",
        "category",
        "itemDesc"
    )
    withdraw_history = db.relationship("WithdrawHistory", back_populates = "items",  cascade="all, delete-orphan")
    def __init__(self,ItemName,ItemAmount,ItemPicture,itemMin,itemDesc):
        self.itemName = ItemName
        self.itemAmount = ItemAmount
        self.itemPicture = ItemPicture
        self.itemMin = itemMin
        self.itemDesc = itemDesc
    
    def generate_qr(self, data: str):
        qr = segno.make(data)
        buffer = BytesIO()
        qr.save(buffer, kind="png")
        qr_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return qr_b64

    def update(self,ItemName,ItemAmount,ItemPicture,itemMin,itemDesc):
        self.itemName = ItemName
        self.itemAmount = ItemAmount
        self.itemPicture = ItemPicture
        self.itemMin = itemMin
        self.itemDesc = itemDesc
        