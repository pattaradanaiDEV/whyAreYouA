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
    IsM_admin = db.Column(db.Boolean, default=False)
    gmail = db.Column(db.String(50), nullable= True)
    phoneNum = db.Column(db.String(10), nullable = True)
    cmuMail = db.Column(db.String(50), nullable = True)
    userpin = db.Column(db.String(255), nullable=True)   # ค่า default = NULL
    availiable = db.Column(db.Boolean,default=False)
    password = db.Column(db.String(255))
    profile_pic = db.Column(db.String(255), nullable=True)
    cart = db.Column(JSON, default=list)
    withdraw_history = db.relationship("WithdrawHistory", back_populates="user")
    
    serialize_only = ("UserID",
                      "Fname",
                      "Lname",
                      "IsM_admin",
                      "availiable",
                      "gmail",
                      "phoneNum",
                      "cmuMail",
                      "userpin",
                      "cart",
                      "profile_pic",
                      "password")

    def __init__(self, Fname, Lname="", phoneNum="", cmuMail="", email="",profile_pic=None,password="",username=""):
        self.Fname = Fname
        self.Lname = Lname
        self.phoneNum = phoneNum
        self.cmuMail = cmuMail
        self.gmail = email
        self.profile_pic=profile_pic
        self.password = password
    
    def update(self,IsM_admin,availiable, cart):
        self.IsM_admin=IsM_admin
        self.availiable=availiable
        self.cart += cart
        
    def set_pin(self, pin):
        self.userpin = generate_password_hash(pin)

    def check_pin(self, pin):
        return check_password_hash(self.userpin, pin)
    
    # def google_login(self, Fname, Lname, email,profile_url):
    #     self.Fname=Fname
    #     self.Lname=Lname
    #     self.gmail=email
    #     self.profile_pic=profile_url
    
    def get_id(self):
        return str(self.UserID)

    def insert_cart(self, itemID, Qualtity):
        self.cart.append([itemID, Qualtity])
