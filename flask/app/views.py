import json
from flask import (jsonify, render_template,
                  request, url_for, flash, redirect)

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



@app.route('/save_pin', methods=['POST'])
def save_pin():
    data = request.get_json()
    pin = data.get("pin")

    if not pin or len(pin) != 6 or not pin.isdigit():
        return jsonify({"success": False, "message": "Invalid PIN"}), 400

    try:
        # ใช้ user จาก session (login)
        user = User.query.get(current_user.UserID)

        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404

        if user.userpin:  
            return jsonify({"success": False, "message": "PIN already set"}), 400

        user.set_pin(pin)       # <-- hash ก่อนเก็บ
        db.session.commit()

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/')
def home():
    return '\
        <style>\
            .a-tag{border: 2px solid gray; border-radius: 5px}\
            .a-tag:link{color: aqua; background-color: gray;}\
            .a-tag:hover{color: aquamarine; background-color: gray;}\
            .a-tag:visited{color: indigo; background-color: gray;}\
            .a-tag:active{color: blue; background-color: gray;}\
        </style>\
        <body style="background-color: black">\
            <div style="text-align: center">\
                <h1 style="color: gray">\
                    Flask says "Hello world!"\
                </h1>\
            </div>\
            <div style="text-align: center">\
                <a href="/homepage" class="a-tag">\
                    Enter homepage\
                </a>\
            </div>\
        </body>'

@app.route('/homepage')
def homepage():
    return render_template('home.html')

@app.route('/signup')
def loginA():
    return render_template('signup.html')

@app.route('/login')
def loginB():
    return render_template('login.html')

@app.route('/createpin')
def create_pin():
    return render_template('createpin.html')

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

@app.route('/newitem')
def newitem():
    return render_template('newitem.html')

@app.route('/stockmenu')
def stockmenu():
    return render_template('stockmenu.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/adminlist', methods=["GET", "POST"])
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

@app.route('/db')
def db_connection():
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return '\
            <style>\
                .a-tag{border: 2px solid gray; border-radius: 5px}\
                .a-tag:link{color: aqua; background-color: gray;}\
                .a-tag:hover{color: aquamarine; background-color: gray;}\
                .a-tag:visited{color: indigo; background-color: gray;}\
                .a-tag:active{color: blue; background-color: gray;}\
            </style>\
            <body style="background-color: black">\
                <div>\
                    <div style="text-align: center">\
                        <h1 style="color:gray">\
                            db works.\
                        </h1>\
                    </div>\
                    <div style="text-align: center">\
                        <a href="/" class="a-tag">\
                            Go back to landing page\
                        </a>\
                    </div>\
                </div>\
            </body>'
    except Exception as e:
        return '\
            <style>\
                .a-tag{border: 2px solid gray; border-radius: 5px}\
                .a-tag:link{color: aqua; background-color: gray;}\
                .a-tag:hover{color: aquamarine; background-color: gray;}\
                .a-tag:visited{color: indigo; background-color: gray;}\
                .a-tag:active{color: blue; background-color: gray;}\
            </style>\
            <body style="background-color: black">\
                <div style="text-align: center">\
                    <h1 style="color:gray">\
                        db is broken. return: 'f"{e}"'\
                    </h1>\
                </div>\
                <div style="text-align: center">\
                    <a href="/" class="a-tag">\
                        Go back to landing page\
                    </a>\
                </div>\
            </body>'

@app.route('/edit')
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
    #return render_template('edit.html', 
    #                       item=R_item,
    #                       user=userID
    #                       )

@app.route('/withdraw')
def withdraw():
    ItemID = request.args.get("itemID")
    userID = request.args.get("userID")
    item = Item.query.filter_by(itemID=ItemID).first()
    return jsonify(item.to_dict())
    #return render_template('edit.html', 
    #                       item=R_item,
    #                       user=userID
    #                       )

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
    
@app.route("/pending_admin", methods=["GET", "POST"])
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
    email = userinfo['email']
    try:
        with db.session.begin():
            user = (User.query.filter_by(gmail=email).with_for_update().first())


            if not user:
                if "family_name" in userinfo:
                    Fname = userinfo['given_name'] 
                    Lname = userinfo['family_name']
                    new_user = User(Fname=Fname, Lname=Lname, email=email)
                else:
                    Fname = userinfo['given_name'] 
                    new_user = User(Fname=Fname, email=email)
                db.session.add(new_user)
                db.session.commit()
    except Exception as ex:
        db.session.rollback()  # Rollback on failure
        app.logger.error(f"ERROR adding new user with email {email}: {ex}")
        return redirect(url_for('loginA'))
  
    user = User.query.filter_by(gmail=email).first()
    login_user(user)
    return redirect('/homepage')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('loginA'))



