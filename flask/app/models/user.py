from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from app import db
from sqlalchemy import DateTime, func
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.withdrawHistory import WithdrawHistory
class User(db.Model, UserMixin, SerializerMixin):
    __tablename__ = "user"
    UserID = db.Column(db.Integer, primary_key=True)
    Fname = db.Column(db.String(24))
    Lname = db.Column(db.String(24))
    IsM_admin = db.Column(db.Boolean, default=False)
    gmail = db.Column(db.String(50))
    phoneNum = db.Column(db.String(10))
    cmuMail = db.Column(db.String(50))
    userpin = db.Column(db.String(255), nullable=True)   # ค่า default = NULL

    withdraw_history = db.relationship("WithdrawHistory", back_populates="user")

    def __init__(self, Fname, Lname, phoneNum, cmuMail):
        self.Fname = Fname
        self.Lname = Lname
        self.phoneNum = phoneNum
        self.cmuMail = cmuMail
        
    def set_pin(self, pin):
        self.userpin = generate_password_hash(pin)

    def check_pin(self, pin):
        return check_password_hash(self.userpin, pin)

    

