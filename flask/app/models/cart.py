from app import db
from sqlalchemy_serializer import SerializerMixin
class Cart(db.Model, SerializerMixin):
    __tablename__ = "cart"

    cartID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    itemID = db.Column(db.Integer, db.ForeignKey("item.itemID"), nullable=False)
    userID = db.Column(db.Integer, db.ForeignKey("user.UserID"), nullable=False)
    quantity = db.Column(db.Integer, default=1)

    user = db.relationship("User", back_populates="cart")
    items = db.relationship("Item", back_populates="cart")

    serialize_only = (
        "cartID",
        "quantity",
        "items.itemID",
        "items.itemName",
        "items.itemPicture",
        
    )

    def __init__(self, user_id, item_id, quantity=1):
        self.userID = user_id
        self.itemID = item_id
        self.quantity = quantity
   

    