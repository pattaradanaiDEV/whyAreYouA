import os
from flask import Flask, request, redirect
from werkzeug.debug import DebuggedApplication
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix 

basedir = os.path.abspath(os.path.dirname(__file__))
root_dir = os.path.dirname(basedir)
load_dotenv(os.path.join(root_dir, '.env.dev'))

app = Flask(__name__, static_folder='static')
app.url_map.strict_slashes = False

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1) 

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'img')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['GOOGLE_CLIENT_ID'] = os.getenv("GOOGLE_CLIENT_ID", None)
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv("GOOGLE_CLIENT_SECRET", None)
app.config['GOOGLE_DISCOVERY_URL'] = os.getenv("GOOGLE_DISCOVERY_URL", None)

app.config['WTF_CSRF_TRUSTED_ORIGINS'] = [
    'https://storagemanage-65ce3.web.app/',
    'https://storagemanage-65ce3.firebaseapp.com/',
]

app.jinja_options = app.jinja_options.copy()
app.jinja_options.update({
    'trim_blocks': True,
    'lstrip_blocks': True
})


app.config['DEBUG'] = True
app.config['SECRET_KEY'] = \
    'cd6b4ac57a1e4ccb3d49c2bdaa7c0399d44b43be698d5a83'
app.config['JSON_AS_ASCII'] = False


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", None)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

csrf = CSRFProtect(app)
csrf.init_app(app)

if app.debug:
    # ตรวจสอบ: DebuggedApplication ควรอยู่หลัง ProxyFix
    app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True) 
# Creating an SQLAlchemy instance
db = SQLAlchemy(app)
oauth = OAuth(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

#ถ้าเกิด circular import ให้ย้ายบรรทัด 40-43 ยกเว้น42 ไปใส่ใน models/init แทน
@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(int(user_id))

@app.before_request
def remove_trailing_slash():
    # Check if the path ends with a slash but is not the root "/"
    if request.path != '/' and request.path.endswith('/'):
        return redirect(request.path[:-1], code=301)

from app import views  # noqa
