from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin, SerializerMixin):
    __tablename__ = "user"
    UserID = db.Column(db.Integer, primary_key=True)
    Fname = db.Column(db.String(24))
    Lname = db.Column(db.String(24))
    IsM_admin = db.Column(db.Boolean, default=False)
    gmail = db.Column(db.String(50), nullable= True)
    phoneNum = db.Column(db.String(10), nullable = True)
    cmuMail = db.Column(db.String(50), nullable = True)
    userpin = db.Column(db.String(255), nullable=True)   # ค่า default = NULL
    availiable = db.Column(db.Boolean,default=False)
    
    cart = db.relationship("Cart", back_populates="user", cascade="all, delete-orphan")
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
                      "cart",)

    def __init__(self, Fname, Lname, phoneNum="", cmuMail="", email=""):
        self.Fname = Fname
        self.Lname = Lname
        self.phoneNum = phoneNum
        self.cmuMail = cmuMail
        self.gmail = email
    
    def update(self,IsM_admin,availiable):
        self.IsM_admin=IsM_admin
        self.availiable=availiable
        
    def set_pin(self, pin):
        self.userpin = generate_password_hash(pin)

    def check_pin(self, pin):
        return check_password_hash(self.userpin, pin)
    
    def google_login(self, Fname, Lname, email):
        self.Fname=Fname
        self.Lname=Lname
        self.gmail=email

    
    def get_id(self):
        return self.UserID
