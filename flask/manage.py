from flask.cli import FlaskGroup

from app import app, db
from app.models.user import User
from app.models.item import Item
from app.models.category import Category
from app.models.withdrawHistory import WithdrawHistory
from app.models.cart import Cart

cli = FlaskGroup(app)

@cli.command("add_history")
def add_history():
    history = WithdrawHistory(user_id=1, item_id=1, quantity=2)
    db.session.add(history)
    db.session.commit()

@cli.command("create_db")
def create_db():
    db.reflect()
    db.drop_all()
    db.create_all()
    db.session.commit()

@cli.command("add_user")
def add_user():
    user = [["Developer","Account","0001000000","DEV-ACC@cmu.ac.th"],
            ["Pongpop","Pongsuk","0000099900","pongpop.pongsuk@cmu.ac.th"],
            ["Santi","Saelee","0000000000","santi.saelee@cmu.ac.th"],
            ["Rui","Jie","0000010000","rui.jie@cmu.ac.th"]]
    for i in user :
        db.session.add(User(Fname=i[0],Lname=i[1],phoneNum=i[2],cmuMail=i[3]))
    db.session.commit()
    User.query.get_or_404(1).IsM_admin=True
    User.query.get_or_404(1).availiable=True
    User.query.get_or_404(2).IsM_admin=True
    User.query.get_or_404(2).availiable=True
    db.session.commit()

@cli.command("seed_db")
def seed_db():
    categories = [
        "Free cate",
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

@cli.command("delete_item")
def delete_item():
    R_item = Item.query.filter_by(cateID=2)
    for i in R_item:
        i["cateID"] = 1
    R_category = Category.query.filter_by(cateID=2).first()
    db.session.delete(R_category)
    db.session.commit()

if __name__ == "__main__":
    cli()