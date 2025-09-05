import json
from flask import (jsonify, render_template,
                  request, url_for, flash, redirect)

from sqlalchemy.sql import text
from app import app
from app import db

@app.route('/')
def home():
    return '\
        <body style="background-color: black">\
            <div style="text-align: center">\
                <h1 style="color: gray">\
                    Flask says "Hello world!\
                </h1>\
            </div>\
        </body>'

@app.route('/db')
def db_connection():
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return '\
            <body style="background-color: black">\
                <div style="text-align: center">\
                    <h1 style="color:gray">\
                        db works.\
                    </h1>\
                </div>\
            </body>'
    except Exception as e:
        return '\
            <body style="background-color: black">\
                <div style="text-align: center">\
                    <h1 style="color:gray">\
                        db is broken. return: 'f"{e}"'\
                    </h1>\
                </div>\
            </body>'




