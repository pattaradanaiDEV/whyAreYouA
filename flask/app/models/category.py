from app import db
from sqlalchemy_serializer import SerializerMixin
class Category(db.Model,SerializerMixin):
    __tablename__ = "category"
    cateID = db.Column(db.Integer, primary_key=True)
    cateName = db.Column(db.String(50))
    items = db.relationship("Item", back_populates="category")
    serialize_only = (
        "cateID",
        "cateName",
    )
    def __init__(self,cateName):
        self.cateName = cateName
    