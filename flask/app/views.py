import json
from flask import (jsonify, render_template,
                  request, url_for, flash, redirect)

from sqlalchemy.sql import text
from app import app
from app import db
from app.models.category import Category

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
                    <h1 style="color: gray">\
                        This is homepage!\
                    </h1>\
                </div>\
                <div style="text-align: center">\
                    <a href="/stockmenu" class="a-tag">\
                        Enter stock menu\
                    </a>\
                </div>\
            </div>\
        </body>'

@app.route('/category')
def category():
    #categories = Category.query.all()
    return render_template('category.html')#, categories=categories)

@app.route('/newstock')
def newstock():
    return render_template('newstock.html')

@app.route('/stockmenu')
def stockmenu():
    return render_template('stockmenu.html')

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