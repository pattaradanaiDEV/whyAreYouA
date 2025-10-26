from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import JSON

class User(db.Model, UserMixin, SerializerMixin):
    __tablename__ = "user"
    UserID = db.Column(db.Integer, primary_key=True)
    Fname = db.Column(db.String(24))
    Lname = db.Column(db.String(24))
    Username = db.Column(db.String(24))
    is_admin = db.Column(db.Boolean, default=False)
    is_sadmin = db.Column(db.Boolean, default=False)
    email = db.Column(db.String(50), nullable= True)
    phoneNum = db.Column(db.String(10), nullable = True)
    available = db.Column(db.Boolean,default=False)
    password = db.Column(db.String(255))
    profile_pic = db.Column(db.String(255), nullable=True)
    
    withdraw_history = db.relationship("WithdrawHistory", back_populates="user", passive_deletes=True)
    cart_items = db.relationship("CartItem", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    notification_statuses = db.relationship("UserNotificationStatus", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    
    serialize_only = ("UserID",
                    "Fname",
                    "Lname",
                    "is_admin",
                    "is_sadmin",
                    "availiable",
                    "email",
                    "phoneNum",
                    "profile_pic",
                    "password",
                    "cart_items.CartID",
                    "cart_items.ItemID",
                    "cart_items.Quantity",
                    "cart_items.Status",)

    def __init__(self, Fname, Lname="", phoneNum="", email="",profile_pic=None,password="",username=""):
        self.Fname = Fname
        self.Lname = Lname
        self.phoneNum = phoneNum
        self.email = email
        self.profile_pic=profile_pic
        self.password = password
    
    def update(self,is_admin,availiable, cart):
        self.is_admin=is_admin
        self.availiable=availiable
        self.cart = cart
    
    def get_id(self):
        return str(self.UserID)

    def insert_cart(self, itemID, quantity, status="w"):
        cart_item = CartItem(UserID=self.UserID, ItemID=itemID, Quantity=quantity, Status=status)
        db.session.add(cart_item)
        return cart_item
    
    def info_update(self, Fname, Lname="", phoneNum="", email="",profile_pic=None,password=""):
        self.Fname = Fname
        self.Lname = Lname
        self.phoneNum = phoneNum
        self.email = email
        if profile_pic != None:
            self.profile_pic=profile_pic
        if password != "":
            self.password = password
