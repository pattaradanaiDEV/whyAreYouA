import json
import os
import io
import base64
import qrcode
import re
from flask import (jsonify, render_template, flash,
                  request, url_for, flash, current_app, abort, session, redirect)
from functools import wraps
from sqlalchemy.sql import text
from app import app
from app import db
from sqlalchemy.orm import outerjoin
from app.models.user_notification_status import UserNotificationStatus
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
from datetime import datetime, timedelta, timezone
from dateutil import tz

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
        if endpoint != 'waiting' or endpoint != 'login':
            return redirect(url_for('waiting'))

    return None


def madmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.IsM_admin:
            pman = User.query.get(2)
            return render_template('forbidden.html', pman = pman)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

@app.route('/get_qr/<int:item_id>')
def get_qr_code(item_id):
    try:
        item = Item.query.get_or_404(item_id)
        qr_data = url_for('scanresult', itemID=item.itemID, _external=True)
        
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        return jsonify({
            'success': True,
            'qr_code_base64': img_str,
            'item_name': item.itemName
        })
    except Exception as e:
        current_app.logger.error(f"Error generating QR for item {item_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
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
        message = f"Item low stock: {item.itemName} (มีจำนวนเหลือแค่ {item.itemAmount} ชิ้น แล้ว)"
        ntype = "⚠️Low_Stock"
        if item.itemAmount == 0 :
            message = f"Item low stock: {item.itemName} (เหลือ 0 ชิ้น แล้ว)"
            ntype="⚠️Item Running Out"
        db.session.add(Notification(
                    user_id=actor_user_id,
                    ntype=ntype,
                    message=message
                ))

@app.route('/')
def landing():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return redirect(url_for('homepage'))

@app.route('/waiting')
def waiting():
    if current_user.availiable == True:
        return redirect(url_for('homepage'))
    return render_template('waiting.html')

@app.route('/homepage')
def homepage():
    cleanup_expired_notifications()

    six_months_ago = datetime.utcnow() - timedelta(days=180)
    top_items_q = (
        db.session.query(
            WithdrawHistory.itemID,
            func.sum(WithdrawHistory.Quantity).label("total_quantity")
        )
        .filter(WithdrawHistory.DateTime >= six_months_ago)
        .group_by(WithdrawHistory.itemID)
        .order_by(func.sum(WithdrawHistory.Quantity).desc())
        .limit(5)
        .all()
    )
    
    top_items = []
    for item_id, total_quantity in top_items_q:
        item = Item.query.get(item_id)
        if item:
            top_items.append({
                "itemID": item.itemID,
                "itemName": item.itemName,
                "itemAmount": item.itemAmount,
                "itemPicture": item.itemPicture,
                "itemMin": item.itemMin,
                "total": int(total_quantity) if total_quantity is not None else 0
            })

    noti_count = 0
    if current_user.is_authenticated:
        now = datetime.now(timezone.utc)
        query = db.session.query(func.count(Notification.id)).outerjoin(
            UserNotificationStatus,
            (Notification.id == UserNotificationStatus.notification_id) &
            (UserNotificationStatus.user_id == current_user.UserID)
        ).filter(
            Notification.expire_at > now,
            (UserNotificationStatus.is_deleted == None) | (UserNotificationStatus.is_deleted == False),
            (UserNotificationStatus.is_read == None) | (UserNotificationStatus.is_read == False)
        )
        noti_count = query.scalar()

    return render_template('home.html', top_items=top_items, noti_count=noti_count)
@app.route('/signin')
def redirect_to_login():
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':

        fname = request.form.get('firstname', '').strip()
        lname = request.form.get('lastname', '').strip()
        phone = request.form.get('phonenumber', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        profile_pic_file = request.files.get('profile_pic')

        if not all([fname, lname, phone, email, password, confirm_password]):
            flash("Please fill in all required fields.")
            return redirect(url_for('signup'))
            
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash("Invalid email address format.")
            return redirect(url_for('signup'))

        if not phone.isdigit():
            flash("Phone number must contain only digits.")
            return redirect(url_for('signup'))
            
        if len(password) < 8:
            flash("Password must be at least 8 characters long.")
            return redirect(url_for('signup'))
        if not re.search(r"[A-Z]", password):
            flash("Password must contain at least one uppercase letter.")
            return redirect(url_for('signup'))
        if not re.search(r"[0-9]", password):
            flash("Password must contain at least one number.")
            return redirect(url_for('signup'))
            
        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for('signup'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("This email is already registered.")
            return redirect(url_for('signup'))

        profile_pic_identifier = None
        if profile_pic_file and profile_pic_file.filename != '':
            profile_pic_identifier = secure_filename(profile_pic_file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], profile_pic_identifier)
            profile_pic_file.save(filepath)
        else:
            profile_pic_identifier = gen_avatar_url(email, fname)

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = User(
            Fname=fname,
            Lname=lname,
            phoneNum=phone,
            email=email,
            password=hashed_password,
            profile_pic=profile_pic_identifier
        )
        db.session.add(new_user)
        db.session.commit()

        db.session.add(Notification(
            user_id=new_user.UserID,
            ntype="request",
            message=f"{new_user.Fname} {new_user.Lname} has requested access to the system."
        ))
        db.session.commit()

        flash("Sign up successful! Please wait for admin approval.")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("User not found. Please try again or sign up.")
            return redirect(url_for('login'))
        
        if not check_password_hash(user.password, password):
            flash("Incorrect password. Please try again.")
            return redirect(url_for('login'))
        
        login_user(user)
        return redirect(url_for('homepage'))
    return render_template('signup.html')

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
    cart_count = CartItem.query.filter_by(UserID=current_user.UserID).count()
    return render_template(
        'category.html',
        categories=categories,
        items=items,
        cart_count=cart_count
    )
    
@app.route('/notification')
@login_required
def notification():
    user_id = current_user.UserID
    now = datetime.now(timezone.utc)
    notifications_with_status = (
        db.session.query(
            Notification,
            UserNotificationStatus.is_read
        )
        .outerjoin(
            UserNotificationStatus,
            (Notification.id == UserNotificationStatus.notification_id) &
            (UserNotificationStatus.user_id == user_id)
        )
        .filter(
            Notification.expire_at > now,
            (UserNotificationStatus.is_deleted == None) | (UserNotificationStatus.is_deleted == False) 
        )
        .order_by(Notification.created_at.desc())
        .all()
    )
    bkk_tz = timezone(timedelta(hours=7))
    
    results = []
    for notif, is_read_status in notifications_with_status:
        local_time = notif.created_at.astimezone(bkk_tz).strftime('%Y-%m-%d %H:%M:%S')
        results.append({
            'id': notif.id,
            'message': notif.message,
            'ntype': notif.ntype,
            'created_at': local_time,
            'is_read': is_read_status if is_read_status is not None else False
        })
    
    return render_template('notification.html', notifications=results)

@app.route('/notification/mark_read/<int:noti_id>', methods=['POST'])
@login_required
def notification_mark_read(noti_id):
    user_id = current_user.UserID
    status = UserNotificationStatus.query.filter_by(user_id=user_id, notification_id=noti_id).first()
    if status:
        status.is_read = True
    else:
        status = UserNotificationStatus(user_id=user_id, notification_id=noti_id)
        status.is_read = True
        db.session.add(status)
    db.session.commit()
    return jsonify({"ok": True})

@app.route('/notification/delete/<int:noti_id>', methods=['POST'])
@login_required
def notification_delete(noti_id):
    user_id = current_user.UserID
    status = UserNotificationStatus.query.filter_by(user_id=user_id, notification_id=noti_id).first()
    if status:
        status.is_deleted = True 
    else:
        status = UserNotificationStatus(user_id=user_id, notification_id=noti_id)
        status.is_deleted = True
        db.session.add(status)
    db.session.commit()
    return jsonify({"ok": True})

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
                        itemMin=int(request.form.get("getmin", 0)),
                        itemDesc=str(request.form.get("getdes", 0)))
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
                        ntype="Withdraw",
                        message=f"{current_user.Fname} {current_user.Lname} ได้เบิก {item.itemName} จำนวน {c.Quantity} ชิ้น"
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
        
        if not user_id:
            flash("User ID is missing.", "danger")
            return redirect(url_for('adminlist'))
            
        user = User.query.get(int(user_id))
        if not user:
            flash("User not found.", "danger")
            return redirect(url_for('adminlist'))

        if action == "promote":
            user.IsM_admin = True
            flash(f"Promoted {user.Fname} to main admin.", "success")
        elif action == "demote":
            user.IsM_admin = False
            flash(f"Demoted {user.Fname} from main admin.", "info")
        elif action == "delete":
            if user.UserID not in [1, 2] and user.UserID != current_user.UserID:
                db.session.delete(user)
                flash(f"User {user.Fname} has been deleted.", "success")
            else:
                flash("This user cannot be deleted.", "danger")

        db.session.commit()
        return redirect(url_for('adminlist'))

    pending_user_count = User.query.filter_by(availiable=False).count()
    users = User.query.filter_by(availiable=True).order_by(User.UserID).all()
    
    return render_template("adminlist.html", users=users, pending_count=pending_user_count)


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
                db.session.add(Notification(
                    ntype="Grant",
                    message=f"คุณ {current_user.Fname} ได้อนุมัติการเข้าใช้งานระบบให้กับคุณ {user.Fname}"
                ))
        
        elif action == "decline" and user_id:
            user = User.query.get(int(user_id))
            if user:
                db.session.delete(user)

        elif action == "accept_all":
            pending_users = User.query.filter_by(availiable=False).all()
            if not pending_users:
                flash("No pending users to accept.", "info")
                return redirect(url_for("pending_user"))
                
            for user in pending_users:
                user.availiable = True
                db.session.add(Notification(
                    ntype="Grant",
                    message=f"คุณ {current_user.Fname} ได้อนุมัติการเข้าใช้งานระบบให้กับคุณ {user.Fname} (อนุมัติทั้งหมด)"
                ))
        
        db.session.commit()
        return redirect(url_for("pending_user"))

    users = User.query.filter_by(availiable=False).all()
    return render_template("pending_admin.html", users=users, pending_count=len(users))

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
                        ntype="Withdraw",
                        message=f"{current_user.Fname} {current_user.Lname} ได้เบิก {item.itemName} จำนวน {quantity} ชิ้น"
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
            cart_item = CartItem.query.filter_by(UserID=current_user.UserID, ItemID=item.itemID, Status='e').first()
            if cart_item:
                if cart_item.Quantity + qty <= item.itemAmount: # currenetAmount <= itemAmount in cart + qty
                    flash("ไม่สามรถป้อนจำนวนที่น้อยกว่าได้", "danger")
                    return redirect(url_for('edit', itemID=item.itemID))
                cart_item.Quantity += qty
            else:
                cart_item = CartItem(UserID=current_user.UserID, ItemID=item.itemID, Quantity=qty, Status='e')
                db.session.add(cart_item)
            db.session.commit()
            flash("เพิ่มเข้าตะกร้าเรียบร้อย", "success")
            return redirect(url_for('category'))

        elif action == "confirm":
            # update database fields
            new_name = request.form.get("getname", item.itemName)
            new_amount = int(request.form.get("getamount", item.itemAmount))
            new_min = int(request.form.get("getmin", item.itemMin if item.itemMin is not None else 0))
            new_cate = request.form.get("getcate")
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
    full_url_for_qr = url_for('scanresult', itemID=item.itemID, _external=True)
    qr_b64 = item.generate_qr(full_url_for_qr)
    return render_template(
        'edit.html',
        item=item,
        QR_Barcode=qr_b64,
        categories=categories
    )

@app.route('/qr_scanner')
@login_required
def qr_scanner(): 
    return render_template('qr_scanner.html')

@app.route('/handle_scan', methods=['POST'])
@login_required
def handle_scan():
    data = request.get_json()
    scanned_url = data.get('scanned_url')

    if not scanned_url:
        return jsonify({'error': 'No URL provided'}), 400

    match = re.search(r'itemID=(\d+)', scanned_url)
    if not match:
        return jsonify({'error': 'Invalid QR code format'}), 400

    item_id = match.group(1)
    
    if current_user.IsM_admin:
        redirect_url = url_for('scanresult', itemID=item_id)
    else:
        redirect_url = url_for('withdraw', itemID=item_id)
        
    return jsonify({'redirect_url': redirect_url})

@app.route('/scanresult')
@login_required
def scanresult():
    """
    แสดงหน้ารายละเอียดสินค้าสำหรับ Admin หลังจากสแกน QR
    UI ตามรูป image_057800.png
    """
    if not current_user.IsM_admin:
        flash("You don't have permission to access this page.", "danger")
        return redirect(url_for('homepage'))
        
    item_id = request.args.get('itemID')
    if not item_id:
        return "Item ID is required", 400

    item = Item.query.get(item_id)
    if not item:
        return "Item not found", 404
        
    return render_template('scan_result.html', item=item)


@app.route('/setting')
def setting():
    return render_template('setting.html')

@app.route('/languages')
def languages():
    return render_template('languages.html')

@app.route('/item/<int:itemID>/withdraw')
def withdraw_byQR(itemID):
    item = Item.query.get_or_404(itemID)
    if item.itemAmount > 0 :
        item.itemAmount -= 1
        history = WithdrawHistory(user_id=None, item_id=itemID, quantity=1)
        db.session.add(history)
        db.session.add(Notification(
                        user_id=current_user.UserID,
                        ntype="Withdraw",
                        message=f"{current_user.Fname} {current_user.Lname} ได้เบิก {item.itemName} จำนวน {quantity}"
                    ))
        create_low_stock_notification_if_needed(item, None)
        db.session.commit()
        return f"เบิก {item.itemName} สำเร็จ"
    else:
        return f"{item.itemName} หมดแล้ว"

@app.route('/delete/item/<int:itemID>', methods=['POST'])
@madmin_required
def delete_item_post(itemID):
    item = Item.query.get(itemID)
    if item:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 404

@app.route('/delete/user/<int:UserID>', methods=['POST'])
def delete_user(UserID):
    user = User.query.get(UserID)
    if user:
        db.session.delete(user)
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
        utc_time = datetime.strptime(i["DateTime"], "%Y-%m-%d %H:%M:%S")
        from_zone = tz.tzutc()
        utc_time = utc_time.replace(tzinfo=from_zone)
        to_zone = tz.tzlocal()
        local_time = str(utc_time.astimezone(to_zone))[0:19] # slice to clear offset (+07:00)
        #local_time = str(utc_time.astimezone(get_localzone()))
        history = {
            "Withdraw date" : local_time,
            "Item Name" : i["items"]["itemName"],
            "Category" : Item.query.get(i["items"]["itemID"]).category.cateName,
            "Quantity" : i["Quantity"]
        }
        list_data.append(history)
    df = pd.DataFrame(list_data)
    output = BytesIO()
    sheet_name = f"WithdrawHistory_{datetime.now().strftime('%Y_%m_%d')}"
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name= sheet_name + ".xlsx",
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
    db_noti_status = UserNotificationStatus.query.all()

    category = list(map(lambda x: x.to_dict(), db_category))
    item = list(map(lambda x:x.to_dict(), db_item))
    users = list(map(lambda x:x.to_dict(), db_user))
    cart = list(map(lambda x:x.to_dict(), db_cart))
    WDhis = list(map(lambda x:x.to_dict(),db_WDhis))
    noti = list(map(lambda x:x.to_dict(),db_noti))
    noti_status = list(map(lambda x:x.to_dict(), db_noti_status))

    forshow=[
        {"Category DB": category},
        {"item DB": item},
        {"User DB": users},
        {"Cart": cart},
        {"Withdraw-History": WDhis},
        {"notification": noti},
        {"notification_status": noti_status} # New entry here
    ]
    return jsonify(forshow)