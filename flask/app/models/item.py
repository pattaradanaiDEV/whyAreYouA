import qrcode
import base64
from io import BytesIO
from app import db
from sqlalchemy_serializer import SerializerMixin

class Item(db.Model,SerializerMixin):
    __tablename__ = "Item"

    itemID = db.Column(db.Integer, primary_key=True)
    cateID = db.Column(db.Integer, db.ForeignKey("stocks_category.cateID"), nullable=False)
    itemAmount = db.Column(db.Integer)
    itemName = db.Column(db.String(100))
    itemPicture = db.Column(db.String(255))
    QR_Barcode = db.Column(db.Text)
    category = db.relationship("Category", back_populates="items")
    withdraw_history = db.relationship("WithdrawHistory", back_populate="Item")
    
    def __init__(self,name,amount,picture):
        self.ItemName = name
        self.ItemAmount = amount
        self.ItemPicture = picture
        self.QR_Barcode = self.generate_qr(name)
    
    def generate_qr(self, data):
        qr = qrcode.make(data)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return qr_b64
        
        
    def update(self,name,amount,picture):
        self.itemName=name
        self.itemAmount=amount
        self.itemPicture=picture
        
