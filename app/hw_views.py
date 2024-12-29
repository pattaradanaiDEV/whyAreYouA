# pattaradanai chaitan (pat)
# 660510667
# sec002

import json
from urllib import request
from urllib.request import urlopen
from flask import jsonify,render_template,redirect,url_for,flash
from app import app
from app.forms import forms

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
    day_left=len(data)-(7-first_day)-1
    num_of_week=day_left//7
    id_fdlw=(7*(day_left//7))+(7-first_day)+1
    return render_template('lab03/hw03_pm25.html',pmData=data,fday=first_day,num_ow=num_of_week,fd_inlw=id_fdlw,dl=day_left,dataLen=len(data))

@app.route('/hw04')
def hw04_rwd():
    return app.send_static_file('hw04_rwd.html')

@app.route('/hw04/aqicard/')
def hw04_aqicard():
    cm="https://api.waqi.info/feed/chiangmai/?token=db32416270f0dbae5bbfbda1974152ab2d1bd961"
    ubon="https://api.waqi.info/feed/Ubon%20Ratchathani/?token=db32416270f0dbae5bbfbda1974152ab2d1bd961"
    pk="https://api.waqi.info/feed/phuket/?token=db32416270f0dbae5bbfbda1974152ab2d1bd961"
    bkk="https://api.waqi.info/feed/bangkok/?token=db32416270f0dbae5bbfbda1974152ab2d1bd961"
    Cnx=json.load(urlopen(cm))
    Ubon=json.load(urlopen(ubon))
    Pk=json.load(urlopen(pk))
    Bkk=json.load(urlopen(bkk))
    #make Cnx Json data
    CnxDateStr=(Cnx['data']['time']['s'].split(" ")[0])
    CnxDate=CnxDateStr.split("-")
    Cnxfc=Cnx['data']['forecast']['daily']['pm25']
    Cnx=mkJson(Cnxfc,CnxDate,CnxDateStr,"Chiang Mai",Cnx['data']['iaqi']['pm25']['v'])
    #make Ubon Json data
    UbonDateStr=(Ubon['data']['time']['s'].split(" ")[0])
    UbonDate=UbonDateStr.split("-")
    Ubonfc=Ubon['data']['forecast']['daily']['pm25']
    Ubon=mkJson(Ubonfc,UbonDate,UbonDateStr,"Ubon Ratchathani",Ubon['data']['iaqi']['pm25']['v'])
    #make Pk Json data
    PkDateStr=(Pk['data']['time']['s'].split(" ")[0])
    PkDate=PkDateStr.split("-")
    Pkfc=Pk['data']['forecast']['daily']['pm25']
    Pk=mkJson(Pkfc,PkDate,PkDateStr,"Phuket",Pk['data']['iaqi']['pm25']['v'])
    #make Bkk Json data
    
    BkkDateStr=(Bkk['data']['time']['s'].split(" ")[0])
    BkkDate=BkkDateStr.split("-")
    Bkkfc=Bkk['data']['forecast']['daily']['pm25']
    Bkk=mkJson(Bkkfc,BkkDate,BkkDateStr,"Bangkok",Bkk['data']['iaqi']['pm25']['v'])
    return render_template('hw04_aqicard.html',data=[Cnx,Ubon,Pk,Bkk])

@app.route('/hw06/register', methods=('GET', 'POST'))
def hw06_register():
    form = forms.RegistrationForm()
    if form.validate_on_submit():
        raw_json = read_file('data/users.json')
        user = json.loads(raw_json)
        for i in range(len(user)):
            if (form.username.data).lower() == user[i]['username']:
                flash('Username already exists')
                return redirect(url_for('hw06_register'))
            elif (form.email.data).lower() == user[i]['email']:
                flash('Email already exists')
                return redirect(url_for('hw06_register'))
           
        user.append({   'username': (form.username.data).lower(),
                        'email': (form.email.data).lower(),
                        'password': form.password.data
                    })
        write_file('data/users.json',
                json.dumps(user, indent=3))
        return redirect(url_for('hw06_users'))
    return render_template('lab06/hw06_register.html', form=form)

@app.route('/hw06/users')
def hw06_users():
    raw_json = read_file('data/users.json')
    user = json.loads(raw_json)
    user_l=len(user)
    return render_template('lab06/hw06_users.html', user=user ,user_l=user_l)

def read_file(filename, mode="rt"):
    with open(filename, mode, encoding='utf-8') as fin:
        return fin.read()

def write_file(filename, contents, mode="wt"):
    with open(filename, mode, encoding="utf-8") as fout:
        fout.write(contents)

def monthName(date,isShort):
    d=date[1]
    m=int(date[0])
    if(m==1):
        if(isShort):
            return "Jan "+d
        return d+" January"
    elif(m==2):
        if(isShort):
            return "Feb "+d
        return d+" February"
    elif(m==3):
        if(isShort):
            return "Mar "+d
        return d+" March"
    elif(m==4):
        if(isShort):
            return "Apr "+d
        return d+" April"
    elif(m==5):
        if(isShort):
            return "May "+d
        return d+" May"
    elif(m==6):
        if(isShort):
            return "June "+d
        return d+" June"
    elif(m==7):
        if(isShort):
            return "July "+d 
        return d+" July"
    elif(m==8):
        if(isShort):
            return "Aug "+d
        return d+" August"
    elif(m==9):
        if(isShort):
            return "Sep "+d
        return d+" September"
    elif(m==10):
        if(isShort):
            return "Oct "+d
        return d+ " October"
    elif(m==11):
        if(isShort):
            return "Nov "+d
        return d+" November"
    else:
        if(isShort):
            return "Dec "+d
        return d+" December"
def findToday(data,currentDate):
    for i in range(len(data)):
        if(data[i]['day']==currentDate):
            return i
def qualityChecker(avg):
    if(avg<=50):
        return "good"
    elif(avg<=100):
        return "moderate"
    elif(avg<=150):
        return "unhealthy-sensitive"
    elif(avg<=200):
        return "unhealthy"
    elif(avg<=300):
        return "very-unhealthy"
    else:
        return "hazardous"
def mkJson(data,today,dayStr,province,aqi):
    return {
        "aqi": aqi,
        "city": province,
        "date": monthName(today[1:],False),
        "year": today[0],
        "forecast": [
            {
            "aqi": data[findToday(data,dayStr)+1]['avg'],
            "day": monthName(data[findToday(data,dayStr)+1]['day'].split('-')[1:],True),
            "quality-class": qualityChecker(data[findToday(data,dayStr)+1]['avg']),
            "quality-class-cap": qualityChecker(data[findToday(data,dayStr)+1]['avg']).capitalize()
            },
            {
            "aqi": data[findToday(data,dayStr)+2]['avg'],
            "day":  monthName(data[findToday(data,dayStr)+2]['day'].split('-')[1:],True),
            "quality-class": qualityChecker(data[findToday(data,dayStr)+2]['avg']),
            "quality-class-cap": qualityChecker(data[findToday(data,dayStr)+2]['avg']).capitalize()
            },
            {
            "aqi": data[findToday(data,dayStr)+3]['avg'],
            "day":  monthName(data[findToday(data,dayStr)+3]['day'].split('-')[1:],True),
            "quality-class": qualityChecker(data[findToday(data,dayStr)+3]['avg']),
            "quality-class-cap": qualityChecker(data[findToday(data,dayStr)+3]['avg']).capitalize()
            }
        ],
        "quality-class": qualityChecker(aqi),
        "quality-class-cap": qualityChecker(aqi).capitalize()
    }
