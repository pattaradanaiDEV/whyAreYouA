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
    
    all_categories = Category.query.all()
    print("✅ Categories seeded:")
    for cat in all_categories:
        print(f"- {cat.cateID}: {cat.cateName}")
## เพิ่ม item เข้า category id = 1
#item = Item(name="Smartphone", amount=10, picture="phone.jpg", min=2)
#item.cateID = 1  # ใส่ FK โดยตรง
#db.session.add(item)
#db.session.commit()
if __name__ == "__main__":
    cli()