# pattaradanai chaitan (pat)
# 660510667
# sec002

import json
from urllib.request import urlopen
from flask import jsonify,render_template
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
    api="https://api.waqi.info/feed/chiangmai/?token=db32416270f0dbae5bbfbda1974152ab2d1bd961"
    apigot=json.load(urlopen(api))
    data=apigot['data']['forecast']['daily']['pm25']
    first_day=int(data[0]['day'].split("-")[-1])
    if( first_day>7 ):
        first_day=first_day%7
    day_left=len(data)-(7-first_day)
    num_of_week=(day_left-1)//7
    id_fdlw=(7*(day_left//7))+(7-first_day)+1
    return render_template('lab03/hw03_pm25.html',pmData=data,fday=first_day,num_ow=num_of_week,fd_inlw=id_fdlw,dl=day_left)
