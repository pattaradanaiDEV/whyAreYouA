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
    for i in range(len(categories)):
        cat = Category(cateName=categories[i])
        db.session.add(cat)
    db.session.commit()




if __name__ == "__main__":
    cli()