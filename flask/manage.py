from flask.cli import FlaskGroup

from app import app, db
from app.models.user import User
from app.models.item import Item
from app.models.category import Category
from app.models.withdrawHistory import WithdrawHistory
from app.models.cart import Cart
from werkzeug.security import generate_password_hash

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

def gen_avatar_url(email, username):
    bgcolor = (generate_password_hash(email, method="sha256") + generate_password_hash(username, method="sha256"))[-6:]
    r = int(bgcolor[0:2], 16)
    g = int(bgcolor[2:4], 16)
    b = int(bgcolor[4:6], 16)
    color = 0.2126 * (r if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4) + \
            0.7152 * (g if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4) + \
            0.0722 * (b if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4)
    avatar_url = ("https://ui-avatars.com/api/?name=" + username + "+&background=" + bgcolor + "&color=" + color)
    return avatar_url

@cli.command("add_user")
def add_user():
    user = [["Developer","Account","0001000000","DEV-ACC@cmu.ac.th","DEV-ACC@cscmumail.com","204361@DEV-ACC"],
            ["Pongpop","Pongsuk","0000099900","pongpop.pongsuk@cmu.ac.th","","PPP@cmu!"],
            ["Santi","Saelee","0000000000","santi.saelee@cmu.ac.th","","TunderEXP001"],
            ["Rui","Jie","0000010000","rui.jie@cmu.ac.th","","MaiMeeRaHatWoi"]]
    for i in user :
        db.session.add(User(Fname=i[0],Lname=i[1],phoneNum=i[2],cmuMail=i[3],email=i[4],profile_pic=gen_avatar_url(i[4], i[0]+i[1]),password=generate_password_hash(i[5])))
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