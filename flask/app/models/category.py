from app import db
from sqlalchemy_serializer import SerializerMixin
class Category(db.Model,SerializerMixin):
    __tablename__ = "Category"


    id = db.Column(db.Integer, primary_key=True)
    cateName = db.Column(db.String(50))
    items = db.relationship("items", back_populates="category")
    def __init__(self,cateName):
        self.cateName = cateName
    