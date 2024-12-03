# pattaradanai chaitan (pat)
# 660510667
# sec002


import json
from urllib.request import urlopen
from flask import jsonify
from app import app




@app.route('/weather')
def hw01_localweather():
    return app.send_static_file('hw01_localweather.html')

@app.route("/api/weather")
def api_weather():
    api="https://api.waqi.info/feed/chiangmai/?token=db32416270f0dbae5bbfbda1974152ab2d1bd961"
    data=json.load(urlopen(api))
    weather = {
        "AQI": data['data']['aqi'],
        "PM10": data['data']['iaqi']['pm10']['v'],
        "PM2.5": data['data']['iaqi']['pm25']['v'],
        "Temperature": data['data']['iaqi']['t']['v'],
        "Time": data['data']['time']['iso']
    }
    return jsonify(weather)

@app.route('/hw03/pm25/')
def hw03_pm25():
    return app.send_static_file('hw03_pm25.html')
