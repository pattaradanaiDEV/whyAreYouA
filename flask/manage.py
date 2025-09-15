from flask.cli import FlaskGroup

from app import app, db
from app.models.item import Item
from app.models.category import Category

cli = FlaskGroup(app)

@cli.command("create_db")
def create_db():
    db.reflect()
    db.drop_all()
    db.create_all()
    db.session.commit()

@cli.command("seed_db")
def seed_db():

    categories = [
        "Stationery",
        "Electrical",
        "IT",
        "Consumables",
        "Tools",
        "Safety Equipment",
        "Medical Equipment",
        "Construction Materials",
        "Machine Parts",
        "Others"
    ]
    for name in categories:
        db.session.add(Category(cateName=name))
    db.session.commit()
    
    item = Item(ItemName="Smartphone", ItemAmount=10, ItemPicture="phone.jpg", itemMin=2)
    item.cateID = 3
    db.session.add(item)
    db.session.commit()
    item = Item(ItemName="pen", ItemAmount=10, ItemPicture="pen.jpg", itemMin=2)
    item.cateID = 1
    db.session.add(item)
    db.session.commit()
if __name__ == "__main__":
    cli()