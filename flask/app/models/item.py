#import qrcode
import base64
from io import BytesIO
from app import db
from sqlalchemy_serializer import SerializerMixin
class Item(db.Model,SerializerMixin):
    __tablename__ = "item"
    itemID = db.Column(db.Integer, primary_key=True)
    cateID = db.Column(db.Integer, db.ForeignKey("category.cateID"), nullable=False)
    itemAmount = db.Column(db.Integer)
    itemName = db.Column(db.String(100))
    itemPicture = db.Column(db.String(255))
    itemMin = db.Column(db.Integer)
    QR_Barcode = db.Column(db.Text)

    category = db.relationship("Category", back_populates="items")
    serialize_only = (
        "itemID",
        "itemName",
        "itemAmount",
        "itemPicture",
        "itemMin",
        "QR_Barcode",
        "category",
    )
    #withdraw_history = db.relationship("WithdrawHistory", back_populates = "items")
    #serialize_only = ("itemID", "itemName", "itemAmount", "itemPicture","itemMin", "QR_Barcode","withdraw_history.WithdrawID","withdraw_history.Quantity","withdraw_history.DateTime" ,"category")
    def __init__(self,name,amount,picture,min):
        self.ItemName = name
        self.ItemAmount = amount
        self.ItemPicture = picture
        self.itemMin = min
        self.QR_Barcode = ""# self.generate_qr(name)
    
    def generate_qr(self, data):
        qr = qrcode.make(data)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return qr_b64
        
        
    def update(self,amount,picture,min):
        self.itemAmount=amount
        self.itemPicture=picture
        self.itemMin=min
        