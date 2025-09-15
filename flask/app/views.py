import json
from flask import (jsonify, render_template,
                  request, url_for, flash, redirect)

from sqlalchemy.sql import text
from app import app
from app import db
from app.models.category import Category
from app.models.user import User
from app.models.item import Item
from flask_login import current_user

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
        is_admin=False
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

@app.route('/adminlist')
def adminlist():
    return render_template('adminlist.html')

@app.route('/test_DB')
def test_DB():
    category = []
    db_category = Category.query.all()


    category = list(map(lambda x: x.to_dict(), db_category))
    app.logger.debug("DB Contacts: " + str(category))


    return jsonify(category)

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
            