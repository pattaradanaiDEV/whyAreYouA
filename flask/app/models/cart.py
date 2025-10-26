from app import db
from sqlalchemy_serializer import SerializerMixin

class CartItem(db.Model, SerializerMixin):
    __tablename__ = "cart_item"
    CartID = db.Column(db.Integer, primary_key=True, autoincrement=True)

    UserID = db.Column(db.Integer, db.ForeignKey("user.UserID"), nullable=False)
    ItemID = db.Column(db.Integer, db.ForeignKey("item.itemID"), nullable=False)
    Quantity = db.Column(db.Integer, nullable=False, default=1)
    Status = db.Column(db.String(1), nullable=False, default="w") # e=edit, w=withdraw
    new_itemName = db.Column(db.String(255), nullable=True)
    new_cateName = db.Column(db.String(50), nullable=True)
    new_itemPicture = db.Column(db.String(255), nullable=True)
    new_itemMin = db.Column(db.Integer, nullable=True)
    new_itemDesc = db.Column(db.String(500), nullable=True)
    user = db.relationship("User", back_populates="cart_items")
    item = db.relationship("Item", back_populates="cart_items")

    serialize_only = (
        "CartID", "UserID", "ItemID", "Quantity", "Status",
        "new_itemName", "new_cateName", "new_itemPicture", 
        "new_itemMin", "new_itemDesc"
    )
    
