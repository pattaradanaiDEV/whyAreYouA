import json
import os
from flask import (jsonify, render_template,
                  request, url_for, flash,current_app, abort,session,redirect)
from functools import wraps
from sqlalchemy.sql import text
from app import app
from app import db
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

#ใช้เพื่อป้องกันคนที่ยังไม่ถูกอนุญาติเข้ามาใช้งาน
@app.before_request
def check_user_availiable():
    except_routes = ['login','test_DB', 'google', 'google_auth','static']
    if request.endpoint and (request.endpoint.startswith('static') or request.endpoint.endswith('.static')):
        return None

    if request.endpoint in except_routes:
        return None

    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    # if not current_user.availiable:
    #     return redirect(url_for('waiting'))
        
def madmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.IsM_admin:
            peeman = User.query.get(2)
            return f"You are not Main_admin please contact {peeman.Fname} {peeman.Lname}"  # Forbidden

        return f(*args, **kwargs)
    return decorated_function

@app.route('/homepage')
def homepage():
    return render_template('home.html')

@app.route('/login')
def login():
    return render_template('signup.html')

@app.route('/category')
def category():
    data_category = Category.query.all()
    categories = [c.to_dict() for c in data_category]

    data_items = Item.query.all()
    items = [i.to_dict() for i in data_items]
    #madmin = current_user.isM_admin if current_user.is_authenticated else False
    return render_template(
        'category.html',
        categories=categories,
        items=items,
        is_admin=True
    )

@app.route('/newitem', methods=["GET", "POST"])
# @madmin_required
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
                        itemMin=999)
            db.session.add(item)
            
            if catename.lower() not in catename_list :
                db.session.add(Category(cateName=catename))
                item.cateID = len(catename_list)+1
            else :
                item.cateID = catename_list.index(catename)+1
                
            db.session.commit()
            return redirect(url_for("test_DB"))
            
    return render_template('newitem.html')

@app.route('/stockmenu')
def stockmenu():
    return render_template('stockmenu.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/adminlist', methods=["GET", "POST"])
# @madmin_required 
# เป็นmain_admin ค่อยเข้าได้นะน้องงง
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
    users = User.query.filter_by(availiable=True).all()
    return render_template("adminlist.html", users=users)

@app.route("/pending_admin", methods=["GET", "POST"])
# @madmin_required
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

@app.route('/edit')
@madmin_required
def edit():
    ItemID = request.args.get("itemID")
    userID = request.args.get("userID")
    item = Item.query.filter_by(itemID=ItemID).first()
    qr_b64 = item.generate_qr(f"http://localhost:56733/item/{item.itemID}/withdraw")
    return render_template(
        'edit.html',
        item=item,
        QR_Barcode=qr_b64
    )

@app.route('/withdraw')
def withdraw():
    ItemID = request.args.get("itemID")
    userID = request.args.get("userID")
    item = Item.query.filter_by(itemID=ItemID).first()
    return jsonify(item.to_dict())

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
                if "family_name" in userinfo:
                    Lname = userinfo.get('family_name', "")
                    new_user = User(Fname=Fname, Lname=Lname, email=email,profile_url=picture)
                else:
                    new_user = User(Fname=Fname, email=email,profile_url=picture)
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
    category = list(map(lambda x: x.to_dict(), db_category))
    db_item = Item.query.all()
    item = list(map(lambda x:x.to_dict(),db_item))
    db_user = User.query.all()
    users = list(map(lambda x:x.to_dict(),db_user))
    forshow=["Category DB",category,"item DB",item,"User DB",users]
    return jsonify(forshow)
