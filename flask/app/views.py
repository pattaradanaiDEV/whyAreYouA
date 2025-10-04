import json
import os
from flask import (jsonify, render_template, flash,
                  request, url_for, flash,current_app, abort,session,redirect)
from functools import wraps
from sqlalchemy.sql import text
from app import app
from app import db
from app.models.cart import CartItem
from app.models.category import Category
from app.models.user import User
from app.models.item import Item
from flask import Blueprint
from app.models.withdrawHistory import WithdrawHistory
from flask_login import login_user, login_required, logout_user, current_user
import pandas as pd
from flask_wtf.csrf import CSRFProtect
from flask import send_file
from io import BytesIO
from app import oauth
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string
from sqlalchemy.orm.attributes import flag_modified
from wtforms.validators import Email

@app.before_request
def check_user_available():
    except_routes = [
        'login',
        'signup',
        'signin',
        'test_DB',
        'google',
        'google_auth',
        'waiting',
        'static' 
    ]
    
    endpoint = request.endpoint
    
    if not endpoint or endpoint.startswith('static') or endpoint in except_routes:
        return None

    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if not current_user.availiable:
        if endpoint != 'waiting':
            return redirect(url_for('waiting'))

    return None

        
def madmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.IsM_admin:
            peeman = User.query.get(2)
            return f"You are not Main_admin please contact {peeman.Fname} {peeman.Lname}"  # Forbidden

        return f(*args, **kwargs)
    return decorated_function

@app.route('/waiting')
def waiting():
    return f"รอก่อนไอ่น้อง"
@app.route('/homepage')
def homepage():
    return render_template('home.html')

@app.route('/signup')
@app.route('/signin')
def redirect_to_login():
    return redirect(url_for('login'))

@app.route('/login', methods=["get", "post"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(gmail=email).first()
        if not user:
            flash("There no such user. Please try again")
            return redirect(url_for('login'))
        if not check_password_hash(user.password, password):
            flash("Incorrect password. Please try again")
            return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('homepage'))
    return render_template('signup.html')

@app.route('/add_user')
def add_user():
    return render_template('add_user.html')

@app.route('/add_user_to_db', methods=['post'])
def add_user_to_db():
    result = request.form.to_dict()

    validated = True
    validated_dict = {}
    valid_keys = ["email", "username", "password"]

    email = validated_dict["email"]
    if not Email()(email):
        flash("Invalid email format")
        return redirect(url_for('signup'))

    for key in result:
        if key not in valid_keys:
            continue

        value = result[key].strip()
        if not value or value == "undefined":
            validated = False
            break
        validated_dict[key] = value

    if validated:
        email = validated_dict["email"]
        username = validated_dict["username"]
        password = validated_dict["password"]
        user = User.query.filter_by(email=email).first()

        if user:
            flash("Email address already in use")
        phoneNum = result["phoneNum"].strip()
        if not phoneNum or phoneNum == "undefined":
            phoneNum = ""

        avatar_url = gen_avatar_url(email, username)
        new_user = User(Fname=username, Lname="", phoneNum=phoneNum, email=email, profile_pic=avatar_url, password=generate_password_hash(password, method="sha256"))

        db.session.add(new_user)
        db.session.commit()

def gen_avatar_url(email, username):
    bgcolor = (generate_password_hash(email, method="sha256") + generate_password_hash(username, method="sha256"))[-6:]
    color = hex(int("0xffffff", 0) - int("0x" + bgcolor, 0)).replace("0x", "")
    avatar_url = ("https://ui-avatars.com/api/?name=" + username + "+&background=" + bgcolor + "&color=" + color)
    return avatar_url

@app.route('/category')
def category():
    data_category = Category.query.all()
    categories = [c.to_dict() for c in data_category]

    data_items = Item.query.order_by(Item.itemID).all()
    items = [i.to_dict() for i in data_items]
    return render_template(
        'category.html',
        categories=categories,
        items=items,
    )

@app.route('/notification')
def notification():
    return render_template('notification.html')

@app.route('/statistic')
def statistic():
    return render_template('statistic.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/newitem', methods=["GET", "POST"])
@madmin_required
def newitem():
    if request.method == "POST":
        action = request.form.get("submit")
        file = request.files.get('file')
        filename = None
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

        if action == "confirm" :
            
            catename = request.form.get("getcate")
            data_category = Category.query.all()
            categories = [c.to_dict() for c in data_category]
            catename_list = [cname['cateName'].lower() for cname in categories]
            item = Item(ItemName=request.form.get("getname"),
                        ItemAmount=request.form.get("getamount"),
                        ItemPicture=filename,
                        itemMin=request.form.get("getmin"))
            db.session.add(item)
            
            if catename.lower() not in catename_list :
                db.session.add(Category(cateName=catename))
                item.cateID = len(catename_list)+1
            else :
                item.cateID = catename_list.index(catename.lower())+1
                
            db.session.commit()
            return redirect(url_for('category'))
    category_list = Category.query.all()
    return render_template('newitem.html',category_list=category_list)

@app.route('/stockmenu')
def stockmenu():
    return render_template('stockmenu.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/adminlist', methods=["GET", "POST"])
@madmin_required 
def adminlist():
    if request.method == "POST":
        action = request.form.get("action")
        user_id = request.form.get("user_id")

        if action == "promote" and user_id:
            user = User.query.get(int(user_id))
            if user:
                user.IsM_admin = True
                db.session.commit()
        else:
            user = User.query.get(int(user_id))
            if user:
                user.IsM_admin = False
                db.session.commit()
    users = User.query.filter_by(availiable=True).order_by(User.UserID).all()
    return render_template("adminlist.html", users=users)

@app.route("/pending_admin", methods=["GET", "POST"])
@madmin_required
def pending_user():
    if request.method == "POST":
        action = request.form.get("action")
        user_id = request.form.get("user_id")

        if action == "accept" and user_id:
            user = User.query.get(int(user_id))
            if user:
                user.availiable = True
                db.session.commit()

        elif action == "decline" and user_id:
            user = User.query.get(int(user_id))
            if user:
                db.session.delete(user)
                db.session.commit()

        elif action == "accept_all":
            users = User.query.filter_by(availiable=False).all()
            for user in users:
                user.availiable = True
            db.session.commit()

        return redirect(url_for("pending_user"))    
    
    users = User.query.filter_by(availiable=False).all()
    return render_template("pending_admin.html", users=users)

@app.route("/withdraw", methods=["GET", "POST"])
def withdraw():
    item_id = int(request.args.get("itemID"))
    action = request.args.get("action", default=None)
    referer = request.args.get("next") or request.referrer or url_for("homepage") #ref หน้าก่อนหน้า
    item = Item.query.filter_by(itemID=item_id).first()
    if not item:
        return "Item not found", 404
    
    if request.method == "POST":
        quantity = int(request.form.get("getQuantity", 0))
        action = request.form.get("action")

        if action == "add-to-cart":
            cart_item = CartItem.query.filter_by(
                UserID=current_user.UserID,
                ItemID=item.itemID,
                Status='w'
            ).first()
            if cart_item:
                cart_item.Quantity += quantity
            else:
                cart_item = CartItem(
                    UserID=current_user.UserID,
                    ItemID=item.itemID,
                    Quantity=quantity,
                    Status='w'
                )
                db.session.add(cart_item)
            db.session.commit()
            return redirect(url_for('category'))

        elif action == "confirm":
            if item.itemAmount >= quantity:
                item.itemAmount -= quantity
                history = WithdrawHistory(
                    user_id=current_user.UserID,
                    item_id=item_id,
                    quantity=quantity
                )
                db.session.add(history)
                db.session.commit()
                #flash(f"เบิก {item.itemName} จำนวน {quantity} สำเร็จ", "success")
            return redirect(url_for('category'))

    return render_template(
        "withdraw.html",
        item=item,
        referer=referer
    )

@app.route('/edit')
@madmin_required
def edit():
    ItemID = request.args.get("itemID")
    cart_item = CartItem.query.filter_by(
        UserID=current_user.UserID,
        ItemID=ItemID,
        Status='e'
    ).first()
    if cart_item:
        cart_item.Quantity += 1
    else:
        cart_item = CartItem(
            UserID=current_user.UserID,
            ItemID=ItemID,
            Quantity=1, 
            Status='e'
        )
        db.session.add(cart_item)
    db.session.commit()
    userID = request.args.get("userID")
    item = Item.query.filter_by(itemID=ItemID).first()
    qr_b64 = item.generate_qr(f"http://localhost:56733/item/{item.itemID}/withdraw")
    return render_template(
        'edit.html',
        item=item,
        QR_Barcode=qr_b64
    )

@app.route('/setting')
def setting():
    return render_template('setting.html')

bp = ("item" , __name__ )
@app.route('/item/<int:itemID>/withdraw')
def withdraw_byQR(itemID):
    item = Item.query.get_or_404(itemID)
    if item.itemAmount > 0 :
        item.itemAmount-=1
        db.session.commit()
        return f"เบิก{item.itemName}สำเร็จ"
    else:
        return f"{item.itemName} หมดแล้วไอน้อง"

@app.route('/delete/item')
@madmin_required
def delete_item():
    return redirect('/category') 

@app.route('/export/withdraw_history')
def export():
    data = WithdrawHistory.query.all()
    data_list = [i.to_dict() for i in data]
    list = []
    for i in data_list:
        print(i)
        history = {
            "Withdraw date" : i["DateTime"],
           # "Username" : user["Fname"] + " " + user["Lname"],
           # "Phone number" : user["phoneNum"],
           # "CMU Mail" : user["cmuMail"],
            "Item Name" : i["items"]["itemName"],
            "Category" : i["items"]["category"]["cateName"],
            "Quantity" : i["Quantity"]
        }
        list.append(history)
    df = pd.DataFrame(list)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="WithdrawHistory")
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="withdraw_History.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
   
@app.route('/google')
def google():
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url=app.config['GOOGLE_DISCOVERY_URL'],
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    redirect_uri = url_for('google_auth', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/google/auth')
def google_auth():
    try:
        token = oauth.google.authorize_access_token()
        #app.logger.debug(str(token))
    except Exception as ex:
        #app.logger.error(f"Error getting token: {ex}")
        return redirect(url_for('homepage'))
    #app.logger.debug(str(token))
    userinfo = token['userinfo']
    app.logger.debug(" Google User " + str(userinfo))
    email = userinfo.get('email')
    picture = userinfo.get('picture', None)
    Fname = userinfo.get('given_name', "")
    try:
        with db.session.begin():
            user = (User.query.filter_by(gmail=email).with_for_update().first())
            if not user:
                password = ''.join(secrets.choice(string.ascii_uppercase + string.digits)
                                for i in range(12))
                if "family_name" in userinfo:
                    Lname = userinfo.get('family_name', "")
                    new_user = User(Fname=Fname, Lname=Lname, email=email,profile_pic=picture, password = password)
                else:
                    new_user = User(Fname=Fname, email=email,profile_pic=picture, password=password)
                db.session.add(new_user)
                db.session.commit()
    except Exception as ex:
        db.session.rollback()  # Rollback on failure
        app.logger.error(f"ERROR adding new user with email {email}: {ex}")
        return redirect(url_for('login'))
  
    user = User.query.filter_by(gmail=email).first()
    login_user(user)
    return redirect('/homepage')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/test_DB')
def test_DB():
    forshow = []
    db_category = Category.query.all()
    db_item = Item.query.order_by(Item.itemID).all()
    db_user = User.query.order_by(User.UserID).all()
    db_cart = CartItem.query.all()
    db_WDhis = WithdrawHistory.query.all()
    category = list(map(lambda x: x.to_dict(), db_category))
    item = list(map(lambda x:x.to_dict(), db_item))
    users = list(map(lambda x:x.to_dict(), db_user))
    cart = list(map(lambda x:x.to_dict(), db_cart))
    WDhis = list(map(lambda x:x.to_dict(),db_WDhis))
    forshow=[{"Category DB":category},{"item DB":item},{"User DB":users},{"Cart":cart},{"Withdraw-History":WDhis}]
    return jsonify(forshow)
