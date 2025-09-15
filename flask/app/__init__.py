import os
from flask import Flask, request, redirect
from werkzeug.debug import DebuggedApplication
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
app = Flask(__name__, static_folder='static')
app.url_map.strict_slashes = False


app.jinja_options = app.jinja_options.copy()
app.jinja_options.update({
    'trim_blocks': True,
    'lstrip_blocks': True
})


app.config['DEBUG'] = True
app.config['SECRET_KEY'] = \
    'cd6b4ac57a1e4ccb3d49c2bdaa7c0399d44b43be698d5a83'
app.config['JSON_AS_ASCII'] = False


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite://")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

csrf = CSRFProtect(app)
csrf.init_app(app)

if app.debug:
    app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)
# Creating an SQLAlchemy instance
db = SQLAlchemy(app)

@app.before_request
def remove_trailing_slash():
   # Check if the path ends with a slash but is not the root "/"
    if request.path != '/' and request.path.endswith('/'):
        return redirect(request.path[:-1], code=301)


from app import views  # noqa