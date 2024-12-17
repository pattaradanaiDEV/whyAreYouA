import datetime
import json
from flask import jsonify, render_template

from app import app
from app import hw_views

@app.route('/')
def home():
    return "Flask says 'Hello world!'"

@app.route('/phonebook')
def index():
    return app.send_static_file('phonebook.html')
# This route serves the dictionary d at the route /data
# This route serves the dictionary d at the route /api/data
@app.route("/api/data")
def data():
    # define some data
    d = {
        "Alice": "(708) 727-2377",
        "Bob": "(305) 734-0429"
    }
    app.logger.debug(str(len(d)) + " entries in phonebook")
    return jsonify(d)  # convert your data to JSON and return

@app.route('/lab02')
def resume():
    return app.send_static_file('lab02_resume.html')

@app.route('/crash')
def crash():
    return 1/0

@app.route('/lab03')
def lab03_home():
    return render_template('lab03/index.html',
                           utc_dt=datetime.datetime.utcnow())

@app.route('/lab03/about/')
def lab03_about():
    return render_template('lab03/about.html')

@app.route('/lab03/comments/')
def lab03_comments():
    raw_json = read_file('data/messages.json')
    messages = json.loads(raw_json)
    return render_template('lab03/comments.html', comments=comments)

@app.route('/lab04')
def lab04_bootstrap():
    return app.send_static_file('lab04_bootstrap.html')






def read_file(filename, mode="rt"):
    with open(filename, mode, encoding='utf-8') as fin:
        return fin.read()




def write_file(filename, contents, mode="wt"):
    with open(filename, mode, encoding="utf-8") as fout:
        fout.write(contents)