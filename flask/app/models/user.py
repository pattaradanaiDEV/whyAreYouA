from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from app import db
from sqlalchemy import DateTime, func

class User(db.Mobel, UserMixin, SerializerMixin):
    __tablename__ = "user"
    UserID = db.Column(db.Integer, primary_key=True)
    Fname = db.Column(db.String(24))
    Lname = db.Column(db.String(24))
    IsM_admin = db.Column(db.Boolean, default=False)
    gmail = db.Column(db.String(50))
    phoneNum = db.Column(db.String(10))
    cmuMail = db.Column(db.String(50))
    withdraw_history = db.relationship("WithdrawHistory", back_populates = "user")

    def __init__(self, Fname, Lname, phoneNum, cmuMail):
        self.Fname = Fname
        self.Lname = Lname
        self.phoneNum = phoneNum
        self.cmuMail = cmuMail

    

