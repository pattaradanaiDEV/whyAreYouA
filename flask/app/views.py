import json
import os
from flask import (jsonify, render_template, flash,
                  request, url_for, flash, current_app, abort, session, redirect)
from functools import wraps
from sqlalchemy.sql import text
from app import app
from app import db
from app.models.cart import CartItem
from app.models.category import Category
from app.models.user import User
from app.models.item import Item
from app.models.withdrawHistory import WithdrawHistory
from app.models.notification import Notification
from flask import Blueprint
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
from sqlalchemy import func
from datetime import datetime, timedelta

# -----------------------
# Helper decorators & functions
# -----------------------
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
        'static',
        'notification',
        'notification_delete',
        'notification_mark_read'
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

def cleanup_expired_notifications():
    """Remove expired notifications from DB"""
    now = datetime.utcnow()
    expired = Notification.query.filter(Notification.expire_at <= now).all()
    if expired:
        for n in expired:
            db.session.delete(n)
        db.session.commit()

def create_low_stock_notification_if_needed(item, actor_user_id=None):
    if item.itemAmount < (item.itemMin if item.itemMin is not None else 0):
        message = f"Item low stock: {item.itemName} ({item.itemAmount} < min {item.itemMin})"
        Notification.create(actor_user_id, "low_stock", message)
        db.session.add(Notification(
                    user_id=actor_user_id,
                    ntype="low_stock",
                    message=message
                ))

@app.route('/')
def landing():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return redirect(url_for('homepage'))

@app.route('/waiting')
def waiting():
    return f"รอก่อนไอ่น้อง"

@app.route('/homepage')
def homepage():
    # cleanup notifications
    cleanup_expired_notifications()

    # Top 5 withdrawn items in last 6 months
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    top_items_q = (
        db.session.query(WithdrawHistory.itemID, func.count(WithdrawHistory.withdrawID).label("total"))
        .filter(WithdrawHistory.DateTime >= six_months_ago)
        .group_by(WithdrawHistory.itemID)
        .order_by(func.count(WithdrawHistory.withdrawID).desc())
        .limit(5)
        .all()
    )
    top_items = []
    for item_id, total in top_items_q:
        item = Item.query.get(item_id)
        if item:
            top_items.append({
                "itemID": item.itemID,
                "itemName": item.itemName,
                "itemAmount": item.itemAmount,
                "itemPicture": item.itemPicture,
                "itemMin": item.itemMin,
                "total": int(total)
            })

    # notification count (unread, non-expired)
    noti_count = 0
    if current_user.is_authenticated:
        noti_count = Notification.query.filter(Notification.is_read == False, Notification.expire_at > datetime.utcnow()).count()

    return render_template('home.html', top_items=top_items, noti_count=noti_count)

@app.route('/signup')
@app.route('/signin')
def redirect_to_login():
    return redirect(url_for('login'))

@app.route('/login', methods=["get", "post"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
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

    # basic validation
    for key in result:
        if key not in valid_keys:
            continue
        value = result[key].strip()
        if not value or value == "undefined":
            validated = False
            break
        validated_dict[key] = value

    if not validated:
        flash("Invalid input")
        return redirect(url_for('signup'))

    email = validated_dict["email"]
    username = validated_dict["username"]
    password = validated_dict["password"]

    user = User.query.filter_by(email=email).first()
    if user:
        flash("Email already used")
        return redirect(url_for('signup'))

    phoneNum = result.get("phoneNum", "").strip()
    avatar_url = gen_avatar_url(email, username)
    new_user = User(Fname=username, Lname="", phoneNum=phoneNum, email=email, profile_pic=avatar_url, password=generate_password_hash(password, method="sha256"))
    db.session.add(new_user)
    db.session.commit()
    db.session.add(Notification(
        user_id=new_user.UserID,
        ntype="request",
        message=f"{new_user.Fname} {new_user.Lname} ได้ขอเข้าใช้งานระบบ"
    ))
    db.session.commit()

    # create signup notification (admins should see)
    flash("User added. Waiting admin approval.")
    return redirect(url_for('login'))

def gen_avatar_url(email, username):
    bgcolor = (generate_password_hash(email, method="sha256") + generate_password_hash(username, method="sha256"))[-6:]
    color = hex(int("0xffffff", 0) - int("0x" + bgcolor, 0)).replace("0x", "")
    avatar_url = ("https://ui-avatars.com/api/?name=" + username + "+&background=" + bgcolor + "&color=" + color)
    return avatar_url

@app.route('/category' ,methods=["GET", "POST"])
def category():
    if request.method == "POST":
        action = request.form.get('action')
        item_id = request.form.get('item_id')
        if action == "delete":
            item = Item.query.get(item_id)
            db.session.delete(item)
            db.session.commit()
            return redirect(url_for('category'))
    data_category = Category.query.all()
    categories = [c.to_dict() for c in data_category]

    data_items = Item.query.order_by(Item.itemID).all()
    items = [i.to_dict() for i in data_items]
    return render_template(
        'category.html',
        categories=categories,
        items=items
    )

@app.route('/notification')
@login_required
@madmin_required
def notification():
    cleanup_expired_notifications()
    notes = Notification.query.filter(Notification.expire_at > datetime.utcnow()).order_by(Notification.created_at.desc()).all()
    notes_dict = [n.to_dict() for n in notes]
    return render_template('notification.html', notifications=notes_dict)

@app.route('/notification/delete/<int:noti_id>', methods=['POST'])
@login_required
@madmin_required
def notification_delete(noti_id):
    n = Notification.query.get(noti_id)
    if n:
        db.session.delete(n)
        db.session.commit()
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 404

@app.route('/notification/mark_read/<int:noti_id>', methods=['POST'])
@login_required
@madmin_required
def notification_mark_read(noti_id):
    n = Notification.query.get(noti_id)
    if n:
        n.is_read = True
        db.session.commit()
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 404

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
                        ItemAmount=int(request.form.get("getamount", 0)),
                        ItemPicture=filename,
                        itemMin=int(request.form.get("getmin", 0)))
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

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    cart_items = (
        CartItem.query
        .filter(CartItem.UserID == current_user.UserID)
        .filter(CartItem.Status.in_(['w', 'e']))
        .all()
    )
    if request.method == 'POST':
        action = request.form.get('action')
        cart_id = request.form.get('cart_id')
        quantity = request.form.get('quantity', type=int)

        if action in ['increase', 'decrease', 'update_input']:
            cart_item = CartItem.query.get(cart_id)
            if not cart_item:
                flash("ไม่พบสินค้าในตะกร้า", "danger")
                return redirect(url_for('cart'))

            item = Item.query.get(cart_item.ItemID)
            if action == 'increase':
                if item and cart_item.Quantity + 1 > item.itemAmount:
                    flash(f"จำนวนเกินสต็อกของ {item.itemName}", "danger")
                    return redirect(url_for('cart'))
                cart_item.Quantity += 1
            elif action == 'decrease' and cart_item.Quantity > 1:
                cart_item.Quantity -= 1
            elif action == 'update_input' and quantity > 0:
                if item and quantity > item.itemAmount:
                    flash(f"จำนวนเกินสต็อกของ {item.itemName}", "danger")
                    return redirect(url_for('cart'))
                cart_item.Quantity = quantity

            db.session.commit()
            flash(f"อัปเดตจำนวนของแล้ว", "success")
            return redirect(url_for('cart'))

        elif action == 'delete':
            cart_item = CartItem.query.get(cart_id)
            if cart_item:
                name = cart_item.item.itemName
                db.session.delete(cart_item)
                db.session.commit()
                flash(f"ลบ {name} ออกจากตะกร้าแล้ว ", "info")
            return redirect(url_for('cart'))

        elif action == 'confirm_cart':
            for c in cart_items:
                item = Item.query.get(c.ItemID)
                if not item:
                    continue
                if c.Status == 'w':
                    if c.Quantity > item.itemAmount:
                        flash(f"ไม่สามารถเบิก {item.itemName} ได้ จำนวนเกินสต็อก", "danger")
                        return redirect(url_for('cart'))
                    item.itemAmount -= c.Quantity
                    history = WithdrawHistory(user_id=current_user.UserID, item_id=item.itemID, quantity=c.Quantity)
                    db.session.add(history)
                    db.session.add(Notification(
                        user_id=current_user.UserID,
                        ntype="withdraw",
                        message=f"{current_user.Fname} {current_user.Lname} ได้เบิก {item.itemName} จำนวน {c.Quantity}"
                    ))
                    create_low_stock_notification_if_needed(item, current_user.UserID)

                elif c.Status == 'e':
                    # items returned from edit (increase stock)
                    item.itemAmount += c.Quantity

                db.session.delete(c)
            db.session.commit()
            flash("ยืนยันตะกร้าเรียบร้อย!", "success")
            return redirect(url_for('cart'))
    return render_template('cart.html', cart_items=cart_items)

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
    item = Item.query.filter_by(itemID=item_id).first()
    if not item:
        return "Item not found", 404

    if request.method == "POST":
        quantity = int(request.form.get("getQuantity", 0))
        action = request.form.get("action")

        # validate
        if quantity <= 0:
            flash("จำนวนต้องมากกว่า 0", "danger")
            return redirect(request.referrer or url_for('category'))

        if action == "add-to-cart":
            if quantity > item.itemAmount:
                flash("จำนวนเกินสต็อก", "danger")
                return redirect(url_for('withdraw', itemID=item_id))
            cart_item = CartItem.query.filter_by(
                UserID=current_user.UserID,
                ItemID=item.itemID,
                Status='w'
            ).first()
            if cart_item:
                # ensure not exceed itemAmount
                if cart_item.Quantity + quantity > item.itemAmount:
                    flash("จำนวนรวมในตะกร้าเกินสต็อก", "danger")
                    return redirect(url_for('withdraw', itemID=item_id))
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
            flash("เพิ่มลงตะกร้าแล้ว", "success")
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
                db.session.add(Notification(
                        user_id=current_user.UserID,
                        ntype="withdraw",
                        message=f"{current_user.Fname} {current_user.Lname} ได้เบิก {item.itemName} จำนวน {quantity}"
                    ))
                create_low_stock_notification_if_needed(item, current_user.UserID)
                db.session.commit()
                flash("เบิกเรียบร้อย", "success")
            else:
                flash("จำนวนในสต็อกไม่เพียงพอ", "danger")
            return redirect(url_for('category'))

    return render_template(
        "withdraw.html",
        item=item
    )

@app.route('/edit', methods=["GET", "POST"])
@madmin_required
def edit():
    ItemID = request.args.get("itemID")
    if not ItemID:
        return redirect(url_for('category'))
    item = Item.query.filter_by(itemID=int(ItemID)).first()
    if not item:
        return "Item not found", 404

    if request.method == "POST":
        action = request.form.get("action")
        # handle file upload
        file = request.files.get('file')
        filename = item.itemPicture
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

        if action == "add-to-cart":
            qty = int(request.form.get("getamount", 1))
            if qty <= 0 or qty > item.itemAmount:
                flash("จำนวนไม่ถูกต้องหรือเกินสต็อก", "danger")
                return redirect(url_for('edit', itemID=item.itemID))
            cart_item = CartItem.query.filter_by(UserID=current_user.UserID, ItemID=item.itemID, Status='e').first()
            if cart_item:
                if cart_item.Quantity + qty > item.itemAmount:
                    flash("จำนวนรวมในตะกร้าเกินสต็อก", "danger")
                    return redirect(url_for('edit', itemID=item.itemID))
                cart_item.Quantity += qty
            else:
                cart_item = CartItem(UserID=current_user.UserID, ItemID=item.itemID, Quantity=qty, Status='e')
                db.session.add(cart_item)
            db.session.commit()
            flash("เพิ่มเข้า cart edit เรียบร้อย", "success")
            return redirect(url_for('category'))

        elif action == "confirm":
            # update database fields
            new_name = request.form.get("getname", item.itemName)
            new_amount = int(request.form.get("getamount", item.itemAmount))
            new_min = int(request.form.get("getmin", item.itemMin if item.itemMin is not None else 0))
            new_cate = request.form.get("getcate")
            # validations
            if new_min > new_amount:
                flash("Item minimum ต้องไม่มากกว่า Item amount", "danger")
                return redirect(url_for('edit', itemID=item.itemID))
            # update
            item.itemName = new_name
            item.itemAmount = new_amount
            item.itemMin = new_min
            item.itemPicture = filename
            # category assignment: try to resolve cateName to id
            if new_cate:
                category = Category.query.filter(func.lower(Category.cateName) == new_cate.lower()).first()
                if category:
                    item.cateID = category.cateID
                else:
                    # create category
                    new_cat = Category(cateName=new_cate)
                    db.session.add(new_cat)
                    db.session.commit()
                    item.cateID = new_cat.cateID
            db.session.commit()
            flash("อัปเดตข้อมูลเรียบร้อย", "success")
            return redirect(url_for('category'))

        elif action == "cancel":
            return redirect(url_for('category'))

    # GET
    # prepare categories for dropdown
    categories = Category.query.order_by(Category.cateID).all()
    qr_b64 = item.generate_qr(f"http://localhost:56733/item/{item.itemID}/withdraw")
    return render_template(
        'edit.html',
        item=item,
        QR_Barcode=qr_b64,
        categories=categories
    )

@app.route('/setting')
def setting():
    return render_template('setting.html')

@app.route('/item/<int:itemID>/withdraw')
def withdraw_byQR(itemID):
    item = Item.query.get_or_404(itemID)
    if item.itemAmount > 0 :
        item.itemAmount -= 1
        history = WithdrawHistory(user_id=None, item_id=itemID, quantity=1)
        db.session.add(history)
        db.session.add(Notification(
                        user_id=current_user.UserID,
                        ntype="withdraw",
                        message=f"{current_user.Fname} {current_user.Lname} ได้เบิก {item.itemName} จำนวน {quantity}"
                    ))
        create_low_stock_notification_if_needed(item, None)
        db.session.commit()
        return f"เบิก {item.itemName} สำเร็จ"
    else:
        return f"{item.itemName} หมดแล้วไอน้อง"

@app.route('/delete/item/<int:itemID>', methods=['POST'])
@madmin_required
def delete_item_post(itemID):
    item = Item.query.get(itemID)
    if item:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 404

@app.route('/delete/item')
@madmin_required
def delete_item():
    return redirect('/category')

@app.route('/export/withdraw_history')
def export():
    data = WithdrawHistory.query.all()
    data_list = [i.to_dict() for i in data]
    list_data = []
    for i in data_list:
        history = {
            "Withdraw date" : i["DateTime"],
            "Item Name" : i["items"]["itemName"],
            "Category" : i["items"]["category"]["cateName"],
            "Quantity" : i["Quantity"]
        }
        list_data.append(history)
    df = pd.DataFrame(list_data)
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
            user = User.query.filter_by(email=email).with_for_update().first()
            if not user:
                password = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for i in range(12))
                Lname = userinfo.get('family_name', "")
                new_user = User(Fname=Fname, Lname=Lname, email=email, profile_pic=picture, password=password)
                db.session.add(new_user)
                db.session.flush()  # ทำให้ new_user.UserID ถูก assign แล้ว

                db.session.add(Notification(
                    user_id=new_user.UserID,
                    ntype="request",
                    message=f"{Fname} {Lname} ได้ขอเข้าใช้งานระบบ"
                ))
    except Exception as ex:
        db.session.rollback()  # Rollback on failure
        app.logger.error(f"ERROR adding new user with email {email}: {ex}")
        return redirect(url_for('login'))

    user = User.query.filter_by(email=email).first()
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
    db_noti = Notification.query.all()
    category = list(map(lambda x: x.to_dict(), db_category))
    item = list(map(lambda x:x.to_dict(), db_item))
    users = list(map(lambda x:x.to_dict(), db_user))
    cart = list(map(lambda x:x.to_dict(), db_cart))
    WDhis = list(map(lambda x:x.to_dict(),db_WDhis))
    noti = list(map(lambda x:x.to_dict(),db_noti))
    forshow=[{"Category DB":category},{"item DB":item},{"User DB":users},{"Cart":cart},{"Withdraw-History":WDhis},{"notification":noti}]
    return jsonify(forshow)
