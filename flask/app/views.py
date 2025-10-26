import json
import os
import io
import base64
import qrcode
import re
from flask import (jsonify, render_template, flash,
                  request, url_for, flash, current_app, abort, session, redirect, send_from_directory,make_response)
from weasyprint import HTML,CSS
from functools import wraps
from sqlalchemy.sql import text
from app import app
from app import db
from sqlalchemy.orm import outerjoin , joinedload
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
from sqlalchemy import func , or_ , and_ 
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
        'serve_sw',
        'serve_manifest',
        'serve_js_from_templates'
    ]

    endpoint = request.endpoint

    if not endpoint or endpoint.startswith('static') or endpoint in except_routes:
        return None

    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if not current_user.available:
        if endpoint != 'waiting' or endpoint != 'login':
            return redirect(url_for('waiting'))

    return None

@app.route('/asset-manifest.json')
def asset_manifest():
    try:
        static_folder = os.path.join(current_app.root_path, 'static')
        assets = [
            '/homepage',
            '/waiting'
        ]

        for root, dirs, files in os.walk(static_folder):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = '/' + os.path.relpath(full_path, current_app.root_path).replace(os.sep, '/')
                assets.append(relative_path)
                
        return jsonify(assets)
    
    except Exception as e:
        current_app.logger.error(f"Error generating asset manifest: {e}")
        return jsonify({"error": str(e)}), 500
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not (current_user.is_admin or current_user.is_sadmin):
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

@app.route('/print_pdf',methods=['POST'])
def print_pdf():
    try:
        data = request.get_json()
        if not data:
            return 'Bad Request: No JSON data', 400
        qr_image_src = data.get('qr_image_src')
        item_name = data.get('item_name', 'Unnamed_Item') # ใส่ค่า default เผื่อไว้
        quantity = int(data.get('quantity',1))
        size = data.get('size','M')
        if not qr_image_src :
            return 'Bad Request: Missing QR code data' , 400
        SIZES = {
            "L":10,
            "M":8,
            "S":5,
            "XS":3,
            "XXS":2
        }
        qr_width_cm = SIZES.get(size,8)
        gutterCm = 0.5
        item_html = f"""
            <div class="qr-item">
                <h5>{item_name}</h5>
                <img src="{qr_image_src}" alt="{qr_image_src}">
            </div>
        """
        all_qrcode_html = item_html * quantity 
        full_html = f"<html><body>{all_qrcode_html}</body></html>"
        css_string = f"""
            <style>
                @page {{
                    size: A4; 
                    margin: 1.5cm; 
                }}
                body {{
                    margin: 0; 
                    padding: 0; 
                    font-family: sans-serif;
                    display: flex;
                    flex-wrap: wrap; 
                    justify-content: flex-start; 
                    align-content: flex-start;
                }}
                    
                
                .qr-item {{
                    width: {qr_width_cm}cm; 
                    margin-right: {gutterCm}cm;
                    margin-bottom: {gutterCm}cm;
                    page-break-inside: avoid; 
                    text-align: center;
                    box-sizing: border-box;
                }}
                h5 {{ 
                    font-size: 8pt; 
                    margin: 0 0 2mm 0; 
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }}
                img {{ 
                    width: 100%; 
                    height: auto; 
                    image-rendering: pixelated; 
                    image-rendering: crisp-edges; 
                }}
            </style>
        """
        html = HTML(string=full_html)
        css = CSS(string=css_string)
        pdf_bytes = html.write_pdf(stylesheets=[css])
        safe_filename = f"{item_name}_printQRcode"
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{safe_filename}_{size}.pdf"'        
        return response
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return 'Internal Server Error' , 500
    
    
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
        message = "m_low"
        ntype = "Low_Stock"
        if item.itemAmount == 0 :
            message = f"m_runout"
            ntype="Item_Running_Out"
        db.session.add(Notification(
                    user_id=actor_user_id,
                    ntype=ntype,
                    message=message,
                    item_id=item.itemID
                ))

@app.route('/service-worker.js')
def serve_sw():
    return send_from_directory(os.path.join(current_app.root_path, 'static'), 'service-worker.js')

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(os.path.join(current_app.root_path, 'static'), 'manifest.json')

@app.route('/js/<path:filename>')
def serve_js_from_templates(filename):
    return send_from_directory(os.path.join(current_app.root_path, 'templates/js'), filename)

@app.route('/')
def landing():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return redirect(url_for('homepage'))

@app.route('/waiting')
def waiting():
    if current_user.available == True:
        return redirect(url_for('homepage'))
    return render_template('waiting.html')

@app.route('/homepage' , methods=['GET', 'POST'])
def homepage():
    cleanup_expired_notifications()
    delta = datetime.utcnow() - timedelta(days=180)
    if request.method == 'POST': 
        select_delta = int(request.form.get("getdelta"))
        if(select_delta < 30):
            flash(f"Change time show to {select_delta} day")
        else:
            flash(f"Change time show to {select_delta//30} month")
        delta = datetime.utcnow() - timedelta(days=select_delta)
    top_items_q = (
        db.session.query(
            WithdrawHistory.itemID,
            func.sum(WithdrawHistory.Quantity).label("total_quantity")
        )
        .filter(WithdrawHistory.DateTime >= delta)
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
            and_(
                Notification.id == UserNotificationStatus.notification_id,
                UserNotificationStatus.user_id == current_user.UserID
            )
        ).filter(
            (Notification.expire_at > now),
            or_(
                Notification.recipient_id == None,
                Notification.recipient_id == current_user.UserID
            ),
            or_(
                UserNotificationStatus.is_deleted == None, 
                UserNotificationStatus.is_deleted == False
            ),
            or_(
                UserNotificationStatus.is_read == None, 
                UserNotificationStatus.is_read == False
            ),
            or_(
                current_user.is_admin == True,
                Notification.ntype.notin_(["Grant", "Request"])
            )
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
            email=email.lower(),
            password=hashed_password,
            profile_pic=profile_pic_identifier
        )
        db.session.add(new_user)
        db.session.commit()

        db.session.add(Notification(
            user_id=new_user.UserID,
            ntype="Request",
            message='m_request'
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
        user = User.query.filter_by(email=email.lower()).first()
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
            if item and item.itemPicture:  
                try:
                    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], item.itemPicture)
                    
                    if os.path.exists(image_path):
                        os.remove(image_path)
                        
                except Exception as e:
                    current_app.logger.error(f"Error deleting image file {item.itemPicture}: {e}")
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
            and_(
                Notification.id == UserNotificationStatus.notification_id,
                UserNotificationStatus.user_id == user_id
            )
        )
        .filter(
            Notification.expire_at > now,
            or_(
                Notification.recipient_id == None,
                Notification.recipient_id == current_user.UserID
            ),
            or_(
                UserNotificationStatus.is_deleted == None, 
                UserNotificationStatus.is_deleted == False
            ),
            or_(
                current_user.is_admin == True,
                Notification.ntype.notin_(["Grant", "Request"])
            )
        )
        .order_by(Notification.created_at.desc())
        .all()
    )
    bkk_tz = timezone(timedelta(hours=7))
    
    results = []
    items = []
    for notif, is_read_status in notifications_with_status:
        local_time = notif.created_at.astimezone(bkk_tz).strftime('%Y-%m-%d %H:%M:%S')
        results.append({
            'id': notif.id,
            'message': notif.message,
            'ntype': notif.ntype,
            'created_at': local_time,
            'is_read': is_read_status if is_read_status is not None else False
        })

        item = Item.query.filter_by(itemID=notif.item_id).first()
        if not item:
            itemName = None
        else:
            itemName = item.itemName
        
        user = User.query.filter_by(UserID=notif.user_id).first()
        if not user:
            Fname = None
            Lname = None
        else:
            Fname = user.Fname
            Lname = user.Lname
        
        r_user = User.query.filter_by(UserID=notif.recipient_id).first()
        if not r_user:
            r_Fname = None
            r_Lname = None
        else:
            r_Fname = r_user.Fname
            r_Lname = r_user.Lname

        items.append({
            'id': notif.id,
            'itemName': itemName,
            'u_Fname': Fname,
            'u_Lname': Lname,
            'r_u_Fname': r_Fname,
            'r_u_Lname': r_Lname
            })
    
    return render_template('notification.html', notifications=results, items=items)

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
    history = db.session.query(WithdrawHistory).order_by(WithdrawHistory.DateTime.desc()).all()
    return render_template('history.html', history = history)

@app.route('/newitem', methods=["GET", "POST"])
@admin_required
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
        .order_by(CartItem.CartID)
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
                if item and (cart_item.Quantity + 1 > item.itemAmount) and cart_item.Status != "e":
                    flash(f"จำนวนเกินสต็อกของ {item.itemName}", "danger")
                    return redirect(url_for('cart'))
                cart_item.Quantity += 1
                
            elif action == 'decrease' and cart_item.Quantity > 1:
                if cart_item.Status == "e" and cart_item.Quantity - 1 <= 0:
                    flash(f"จำนวนไม่ถูกต้อง")
                    return redirect(url_for('cart'))
                cart_item.Quantity -= 1
                
            elif action == 'update_input' and quantity > 0:
                if item and (quantity > item.itemAmount) and cart_item.Status != "e":
                    cart_item.Quantity = item.itemAmount
                    flash(f"จำนวนเกินสต็อกของ {item.itemName}", "danger")
                    db.session.commit()
                    return redirect(url_for('cart'))
                cart_item.Quantity = quantity

            db.session.commit()
            flash(f"อัปเดตจำนวนของแล้ว", "success")
            return redirect(url_for('cart'))
        elif action == 'update_details':
            cart_item = CartItem.query.get(cart_id)
            if not cart_item or cart_item.Status != 'e':
                flash("ไม่สามารถอัปเดตรายการนี้ได้", "danger")
                return redirect(url_for('cart'))
            cart_item.new_itemName = request.form.get('new_itemName')
            cart_item.new_cateName = request.form.get('new_cateName')
            cart_item.new_itemMin = request.form.get('new_itemMin', type=int)
            cart_item.new_itemDesc = request.form.get('new_itemDesc')
            new_quantity = request.form.get('quantity', type=int)
            if new_quantity is not None and new_quantity >= 0:
                cart_item.Quantity = new_quantity
            else:
                flash("จำนวนที่เพิ่มไม่ถูกต้อง", "danger")
                return redirect(url_for('cart'))
            file = request.files.get('new_itemPicture')
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                cart_item.new_itemPicture = filename
            db.session.commit()
            flash(f"อัปเดตรายละเอียด {cart_item.new_itemName} ในตะกร้าแล้ว", "success")
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
                        c.Quantity = item.itemAmount
                        flash(f"ไม่สามารถเบิก {item.itemName} ได้ จำนวนเกินสต็อก", "danger")
                        db.session.commit()
                        return redirect(url_for('cart'))
                    item.itemAmount -= c.Quantity
                    history = WithdrawHistory(user_id=current_user.UserID, item_id=item.itemID, quantity=c.Quantity)
                    db.session.add(history)
                    db.session.add(Notification(
                        user_id=current_user.UserID,
                        ntype="Withdraw",
                        message='m_withdraw,'+str(item.itemAmount)+','+str(c.Quantity),
                        item_id=item.itemID
                    ))
                    create_low_stock_notification_if_needed(item, current_user.UserID)

                elif c.Status == 'e':
                    item.itemName = c.new_itemName
                    item.itemMin = c.new_itemMin
                    item.itemDesc = c.new_itemDesc
                    if c.new_itemPicture != item.itemPicture:
                        if item.itemPicture and not item.itemPicture.startswith(('http:','https:')):
                            try:
                                old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], item.itemPicture)
                                if os.path.exists(old_path):
                                    os.remove(old_path)
                            except Exception as e:
                                current_app.logger.error(f"Error deleting old pic: {e}")

                        item.itemPicture = c.new_itemPicture #place picture
                    if c.new_cateName:
                        category = Category.query.filter(func.lower(Category.cateName) == c.new_cateName.lower()).first()
                        if category:
                            item.cateID = category.cateID
                        else:
                            new_cat = Category(cateName=c.new_cateName)
                            db.session.add(new_cat)
                            db.session.flush()
                            item.cateID = new_cat.cateID
                    item.itemAmount += c.Quantity

                db.session.delete(c)
            db.session.commit()
            flash("ยืนยันตะกร้าเรียบร้อย!", "success")
            return redirect(url_for('cart'))
    category_list = Category.query.order_by(Category.cateName).all()
    return render_template('cart.html', cart_items=cart_items,category_list=category_list)

@app.route('/manage_user', methods=["GET", "POST"])
@admin_required
def manage_user():
    if request.method == "POST":
        action = request.form.get("action")
        user_id = request.form.get("user_id")
        
        if not user_id:
            flash("User ID is missing.", "danger")
            return redirect(url_for('manage_user'))
            
        user = User.query.get(int(user_id))
        if not user:
            flash("User not found.", "danger")
            return redirect(url_for('manage_user'))

        if action == "promote":
            user.is_admin = True
            db.session.add(Notification(
                    user_id=current_user.UserID,
                    ntype="Promoted",
                    recipient_id=user.UserID,
                    message="m_promote"
                ))
            flash(f"Promoted {user.Fname} to main admin.", "success")
        elif action == "demote":
            user.is_admin = False
            db.session.add(Notification(
                    user_id=current_user.UserID,
                    ntype="Demoted",
                    recipient_id=user.UserID,
                    message="m_demote"
                ))
            flash(f"Demoted {user.Fname} from main admin.", "info")
        elif action == "delete":
            if not user.is_sadmin and user.UserID != current_user.UserID: 
                if user and user.profile_pic:  
                    try:
                        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], user.profile_pic)
                        
                        if os.path.exists(image_path):
                            os.remove(image_path)
                            
                    except Exception as e:
                        current_app.logger.error(f"Error deleting image file {user.profile_pic}: {e}")
                db.session.delete(user)
                flash(f"User {user.Fname} has been deleted.", "success")
            else:
                flash("This user cannot be deleted.", "danger")

        db.session.commit()
        return redirect(url_for('manage_user'))

    pending_user_count = User.query.filter_by(available=False).count()
    users = User.query.filter_by(available=True).order_by(User.UserID).all()
    
    return render_template("manage_user.html", users=users, pending_count=pending_user_count)

@app.route("/admin_contact", methods=["GET", "POST"])
@login_required
def admin_contact():
    #admin = User.query.filter_by(is_admin=True).order_by(User.UserID).all()
    return render_template("admin_contact.html",)

@app.route("/pending_user", methods=["GET", "POST"])
@admin_required
def pending_user():
    if request.method == "POST":
        action = request.form.get("action")
        user_id = request.form.get("user_id")

        if action == "accept" and user_id:
            user = User.query.get(int(user_id))
            if user:
                user.available = True
                db.session.add(Notification(
                    ntype="Grant",
                    message='m_grant',
                    user_id=user_id,
                    recipient_id=current_user.UserID
                ))
                db.session.add(Notification(
                    user_id=current_user.UserID,
                    recipient_id=user.UserID,
                    ntype="Access_Granted",
                    message="m_access"
                ))
        
        elif action == "decline" and user_id:
            user = User.query.get(int(user_id))
            if user:
                if user.profile_pic:  
                    try:
                        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], user.profile_pic)
                        
                        if os.path.exists(image_path):
                            os.remove(image_path)
                            
                    except Exception as e:
                        current_app.logger.error(f"Error deleting image file {user.profile_pic}: {e}")
                db.session.delete(user)
                flash(f"User {user.Fname} has been deleted.", "success")
                db.session.delete(user)

        elif action == "accept_all":
            pending_users = User.query.filter_by(available=False).all()
            if not pending_users:
                flash("No pending users to accept.", "info")
                return redirect(url_for("pending_user"))
                
            for user in pending_users:
                user.available = True
                db.session.add(Notification(
                    ntype="Grant",
                    message='m_grant'
                ))
                db.session.add(Notification(
                    user_id=current_user.UserID,
                    recipient_id=user.UserID,
                    ntype="Access_Granted",
                    message=f"m_access"
                ))
        
        db.session.commit()
        return redirect(url_for("pending_user"))

    users = User.query.filter_by(available=False).all()
    return render_template("pending_user.html", users=users, pending_count=len(users))

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
                        message='m_withdraw,'+str(item.itemAmount)+','+str(quantity),
                        item_id=item.itemID
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
@admin_required
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
            try:
                new_name = request.form.get("getname", item.itemName)
                new_cate = request.form.get("getcate")
                new_min = int(request.form.get("getmin", item.itemMin if item.itemMin is not None else 0))
                new_desc = request.form.get("getdes", item.itemDesc)
                fill_amount = int(request.form.get("getamount", item.itemAmount))
                cart_item = CartItem.query.filter_by(
                    UserID=current_user.UserID, 
                    ItemID=item.itemID, 
                    Status='e'
                ).first()
                if cart_item:
                    cart_item.new_itemName = new_name
                    cart_item.new_cateName = new_cate
                    cart_item.new_itemMin = new_min
                    cart_item.new_itemDesc = new_desc
                    cart_item.new_itemPicture = filename
                    cart_item.Quantity += fill_amount 
                    db.session.commit()
                    flash(f"อัปเดตรายการแก้ไขในตะกร้า (เพิ่มอีก {fill_amount} ชิ้น)", "success")
                else:
                    cart_item = CartItem(
                        UserID=current_user.UserID,
                        ItemID=item.itemID,
                        Quantity=fill_amount,
                        Status='e',
                        new_itemName=new_name,
                        new_cateName=new_cate,
                        new_itemMin=new_min,
                        new_itemDesc=new_desc,
                        new_itemPicture=filename
                    )
                    db.session.add(cart_item)
                    flash(f"เพิ่มรายการแก้ไข (เติม {fill_amount} ชิ้น) ลงในตะกร้า", "success")
                    
                    db.session.commit()
                    return redirect(url_for('category'))
            except ValueError:
                flash("จำนวนไม่ถูกต้อง", "danger")
                return redirect(url_for('edit', itemID=item.itemID))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error in edit/add-to-cart: {e}")
                flash(f"เกิดข้อผิดพลาด: {e}", "danger")
                return redirect(url_for('edit', itemID=item.itemID))

        else:
            new_name = request.form.get("getname", item.itemName)
            new_amount = item.itemAmount+int(request.form.get("getamount", item.itemAmount))
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
    
    if (current_user.is_admin or current_user.is_sadmin):
        redirect_url = url_for('scanresult', itemID=item_id)
    else:
        redirect_url = url_for('withdraw', itemID=item_id)
        
    return jsonify({'redirect_url': redirect_url})

@app.route('/scanresult')
@login_required
def scanresult():
    if not (current_user.is_admin or current_user.is_sadmin):
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

@app.route('/appearance')
def appearance():
    return render_template('appearance.html')

@app.route('/delete/user/<int:UserID>', methods=['POST'])
def delete_user(UserID):
    user = User.query.get(UserID)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 404

@app.route('/delete/item')
@admin_required
def delete_item():
    return redirect('/category')

@app.route('/export/withdraw_history')
def export():
    if (current_user.is_admin) :
        data = (
            db.session.query(WithdrawHistory)
            .options(
                joinedload(WithdrawHistory.user),  # โหลด User ที่เกี่ยวข้อง
                joinedload(WithdrawHistory.items).joinedload(Item.category) # โหลด Item และ Category ของ Item
            )
            .order_by(WithdrawHistory.DateTime.desc()) 
            .all()
        )
    else:
        data = (
            db.session.query(WithdrawHistory)
            .options(
                joinedload(WithdrawHistory.user),  # โหลด User ที่เกี่ยวข้อง
                joinedload(WithdrawHistory.items).joinedload(Item.category) # โหลด Item และ Category ของ Item
            )
            .order_by(WithdrawHistory.DateTime.desc()) 
            .filter(WithdrawHistory.UserID == current_user.UserID)
            .all()
        )
    list_data = []
    to_zone = tz.tzlocal()
    for wh in data:
        
        if wh.DateTime:
            local_dt = wh.DateTime.astimezone(to_zone)
            local_date = local_dt.strftime('%Y-%m-%d')
            local_time = local_dt.strftime('%H:%M:%S')
        user_name = f"{wh.user.Fname} {wh.user.Lname}"
        user_email = wh.user.email
        item_name = wh.items.itemName
        category_name = wh.items.category.cateName if wh.items and wh.items.category else "N/A"

        history = {
            "Withdraw date" : local_date,
            "Withdraw time" : local_time,
            "Item Name" : item_name,
            "Category" : category_name,
            "Quantity" : wh.Quantity,
            "User ID" : wh.UserID if wh.UserID else "N/A",
            "User name" : user_name,
            "User email" : user_email
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

@app.route('/export/stock')
def exportStock():
    data = (
            db.session.query(Item)
            .order_by(Item.itemID) 
            .all()
        )
    list_data = []
    for i in data:
        Item_data = {
            "Item ID":i.itemID,
            "ItemName":i.itemName,
            "ItemAmount":i.itemAmount,
            "ItemMinimun":i.itemMin,
            "Description":i.itemDesc,
            "Category ID":i.category.cateID,
            "Category name":i.category.cateName

        }
        list_data.append(Item_data)
    df = pd.DataFrame(list_data)
    output = BytesIO()
    sheet_name = f"Stock_{datetime.now().strftime('%Y_%m_%d')}"
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
            user = User.query.filter_by(email=email.lower()).with_for_update().first()
            if not user:
                password = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for i in range(12))
                Lname = userinfo.get('family_name', "")
                new_user = User(Fname=Fname, Lname=Lname, email=email.lower(), profile_pic=picture, password=password)
                db.session.add(new_user)
                db.session.flush()  # ทำให้ new_user.UserID ถูก assign แล้ว

                db.session.add(Notification(
                    user_id=new_user.UserID,
                    ntype="Request",
                    message="m_request"
                ))
                db.session.commit()

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

@app.route('/cate_edit' ,methods=["GET", "POST"])
@admin_required
def cate_edit():
    cate = Category.query.order_by(Category.cateID).all()
    items = Item.query.all()
    if request.method == "POST":
        action = request.form.get('action')
        cate_id = request.form.get('cate_id')
        if action == "delete":
            R_item = Item.query.filter_by(cateID=cate_id)
            for i in R_item:
                i.cateID = 1
            R_category = Category.query.filter_by(cateID=cate_id).first()
            db.session.delete(R_category)
            db.session.commit()
            return redirect(url_for('cate_edit'))

    return render_template("edit_cate.html", cate=cate, items=items)

@app.route('/profile_edit', methods=["GET", "POST"])
@login_required
def profile_edit():
    if request.method == 'POST':
        fname = request.form.get('firstname', '').strip()
        lname = request.form.get('lastname', '').strip()
        phone = request.form.get('phonenumber', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        profile_pic_file = request.files.get('profile_pic')

        key_list = ["firstname", "lastname", "phonenumber", "email"]
        kay_list = ["Fname", "Lname", "phoneNum", "email"]
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash("Invalid email address format.")
            return redirect(url_for('profile_edit'))

        if not phone.isdigit():
            flash("Phone number must contain only digits.")
            return redirect(url_for('profile_edit'))
            
        if password:  # Check if they want to change their password
            # key_list.append("password")
            # kay_list.append("password")
            if len(password) < 8:
                flash("Password must be at least 8 characters long.")
                return redirect(url_for('profile_edit'))
            if not re.search(r"[A-Z]", password):
                flash("Password must contain at least one uppercase letter.")
                return redirect(url_for('profile_edit'))
            if not re.search(r"[0-9]", password):
                flash("Password must contain at least one number.")
                return redirect(url_for('profile_edit'))
            if password != confirm_password:
                flash("Passwords do not match.")
                return redirect(url_for('profile_edit'))

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        valid_dict = dict()
        value = request.form.to_dict()
        for i in range(len(key_list)):
            valid_dict[kay_list[i]] = value[key_list[i]]
        if password: # Truly shit coding style by yours truly <3
            valid_dict["password"] = hashed_password
        if profile_pic_file:
            profile_pic_identifier = secure_filename(profile_pic_file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], profile_pic_identifier)
            profile_pic_file.save(filepath)
            valid_dict["profile_pic"] = profile_pic_identifier
        # app.logger.debug(valid_dict)
        try:
            boi = User.query.get(int(current_user.UserID))
            if boi:
                boi.info_update(**valid_dict)
            db.session.commit()
            return redirect(url_for('homepage'))
        
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Database error: {str(e)}")
            return render_template("profile_edit.html")


    return render_template("profile_edit.html")


