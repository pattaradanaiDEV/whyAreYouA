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
    
    item = Item(ItemName="Ballpoint Pen", ItemAmount=120, ItemPicture="Ballpoint_Pen.jpg", itemMin=60)
    item.cateID = 1
    db.session.add(item)
    item = Item(ItemName="Notebook A5", ItemAmount=75, ItemPicture="Notebook_A5.jpg", itemMin=30)
    item.cateID = 1
    db.session.add(item)
    item = Item(ItemName="Highlighter Set", ItemAmount=30, ItemPicture="Highlighter_Set.jpg", itemMin=15)
    item.cateID = 1
    db.session.add(item)
    item = Item(ItemName="Stapler", ItemAmount=20, ItemPicture="Stapler.jpg", itemMin=10)
    item.cateID = 1
    db.session.add(item)
    item = Item(ItemName="Paper Clips Box", ItemAmount=50, ItemPicture="Paper_Clips_Box.jpg", itemMin=25)
    item.cateID = 1
    db.session.add(item)
    item = Item(ItemName="Laptop Dell XPS", ItemAmount=10, ItemPicture="Laptop_Dell_XPS.jpg", itemMin=5)
    item.cateID = 3
    db.session.add(item)
    item = Item(ItemName="Wireless Mouse", ItemAmount=40, ItemPicture="Wireless_Mouse.jpg", itemMin=20)
    item.cateID = 3
    db.session.add(item)
    item = Item(ItemName="Mechanical Keyboard", ItemAmount=25, ItemPicture="Mechanical_Keyboard.jpg", itemMin=12)
    item.cateID = 3
    db.session.add(item)
    item = Item(ItemName="External HDD 1TB", ItemAmount=15, ItemPicture="External_HDD_1TB.jpg", itemMin=7)
    item.cateID = 3
    db.session.add(item)
    item = Item(ItemName="Monitor 24", ItemAmount=10, ItemPicture="Monitor_24.jpg", itemMin=5)
    item.cateID = 3
    db.session.add(item)
    item = Item(ItemName="Hammer", ItemAmount=18, ItemPicture="Hammer.jpg", itemMin=20)
    item.cateID = 5
    db.session.add(item)
    item = Item(ItemName="Screwdriver Set", ItemAmount=25, ItemPicture="Laptop_Dell_XPS.jpg", itemMin=10)
    item.cateID = 5
    db.session.add(item)
    item = Item(ItemName="Wrench", ItemAmount=12, ItemPicture="Wrench.jpg", itemMin=5)
    item.cateID = 5
    db.session.add(item)
    item = Item(ItemName="Electric Drill", ItemAmount=8, ItemPicture=" Electric_Drill.jpg", itemMin=8)
    item.cateID = 5
    db.session.add(item)
    item = Item(ItemName="Tape Measure", ItemAmount=30, ItemPicture="Tape_Measure.jpg", itemMin=15)
    item.cateID = 5
    db.session.add(item)
    db.session.commit()
if __name__ == "__main__":
    cli()