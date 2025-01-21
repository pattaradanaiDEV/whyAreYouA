from flask import Flask


app = Flask(__name__, static_folder='static')
app.url_map.strict_slashes = False


app.jinja_options = app.jinja_options.copy()
app.jinja_options.update({
    'trim_blocks': True,
    'lstrip_blocks': True
})

app.config['DEBUG'] = True
app.config['JSON_AS_ASCII'] = False
app.config['SECRET_KEY'] = \
    '4b81b99132ad25fa7bf6ea42af95889ca6dcf6ccd36c00aa'


from app import views  # noqa
