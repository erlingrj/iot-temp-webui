from flask import Flask, request, render_template, session, redirect, flash, Response
from aws_controller import DecimalEncoder
import aws_controller
import json
import datetime
import os
from sqlalchemy.orm import sessionmaker
from tabledef import *
engine = create_engine('sqlite:///users.db', echo=True)


DBG = True

CURRENT_PATH='current.txt'


app = Flask(__name__)
app._static_folder = 'static'
app.secret_key = os.urandom(12)
EntryType = {
    'TEMP' : 0,
    'CONTROL' : 1
}

@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:

        current_temp = aws_controller.db_get_last_temp(session.get('CustomerID'))
        if current_temp:
            current_temp = current_temp['Data']
        current_control = aws_controller.db_get_last_control(session['CustomerID'])
        if current_control:
            current_control = [float(i) for i in current_control['Data'].split('-')]
        else:
            current_control = [None] * 12

        return render_template('index.html', current_temp=current_temp, current_control=current_control)

@app.route('/login', methods = ['POST'])
def login():

    Session = sessionmaker(bind=engine)
    s = Session()
    query = s.query(User).filter(User.username.in_([request.form['username']]), User.password.in_([request.form['password']]) )
    result = query.first()
    if result:
        session['logged_in'] = True
        session['CustomerID'] = result.id
        session['APIKEY'] = result.apikey
    else:
        flash('Wrong password!')
    return index()

@app.route('/stats')
def stats():
    # Here we will display the historical stuff
    # Maybe make some interesting plots?
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        last24, lastw = aws_controller.db_get_stats(session.get('CustomerID'))
        
        return render_template('stats.html', data24h=last24, data1w=lastw)

@app.route('/control')
def new_control_policy():
    # When the user wishes to make a new control policy
    # He will end up in this page

    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        current_control = aws_controller.db_get_last_control(session.get('CustomerID'))
        if current_control:
            current_control = [float(i) for i in current_control['Data'].split('-')]
        else:
            current_control = [18.0 for i in range(0,12)]
        
        print(session.get('APIKEY'))
        return render_template('control.html', control_policy = current_control, APIKEY=session.get('APIKEY'))

@app.route('/about')
def about():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('about.html')



@app.route('/logout')
def logout():
    session['logged_in'] = False
    session['CustomerID'] = None
    session['APIKEY'] = None

    return render_template('login.html')
# Endpoint for running tests on user-db etc.
@app.route('/test')
def test():

    POST_USERNAME = "user"
    POST_PASSWORD = "user"

    Session = sessionmaker(bind=engine)
    s = Session()
    query = s.query(User).filter(User.username.in_([POST_USERNAME]), User.password.in_([POST_PASSWORD]) )
    result = query.first()
    print(result.apikey)
    print(result.username)
    print(result.id)
    if result:
        return "Object found"
    else:
        return "Object not found " + POST_USERNAME + " " + POST_PASSWORD





###################################################
#                                                 #
#           API TO THE DATABASE FOR RPI           #
#                                                 #
###################################################


@app.route('/db/get-last-temp', methods=["GET"])
def get_last_temp():
    #Validate APIKEY
    Session = sessionmaker(bind=engine)
    s = Session()
    query = s.query(User).filter(User.apikey.in_([request.headers['APIKEY']]))
    result = query.first()
    if result:
        return json.dumps(aws_controller.db_get_last_temp(result.id), cls=DecimalEncoder)
    else:
        return Response("Invalid APIKEY", status=201, mimetype='text')

@app.route('/db/get-last-control', methods=['GET'])
def get_last_control():
    # Validate APIKey
    Session = sessionmaker(bind=engine)
    s = Session()
    query = s.query(User).filter(User.apikey.in_([request.headers['APIKEY']]))
    result = query.first()
    if result:
        return json.dumps(aws_controller.db_get_last_control(result.id), cls=DecimalEncoder)
    else:
        return Response("Invalid APIKEY", status=201, mimetype='text')

@app.route('/db/post-temp', methods=['POST'])
def post_temp():
    content =  request.get_json()
    if DBG:
        print(content)
    
    #Validate APIKEY
    Session = sessionmaker(bind=engine)
    s = Session()
    query = s.query(User).filter(User.apikey.in_([content['APIKEY']]))
    result = query.first()

    #Validate the API-KEY
    #TODO: Make a mapping between APIKEYS and CustomerIDs
    if result:
        if DBG:
            print("APIKEY found")
        # Update CustomerID field
        content['CustomerID'] = result.id
        content['EntryID'] = EntryType['TEMP']
        
        # Send content to aws controller
        response = aws_controller.db_post(content)
    else:
        response = -1
    
    if response != -1:
        return "SUCCESS"
    else:
        return "FAIL"

@app.route('/db/post-control', methods=['POST'])
def post_control():
    content =  request.get_json()
    if DBG:
        print(content)

    #Validate APIKEY
    Session = sessionmaker(bind=engine)
    s = Session()
    query = s.query(User).filter(User.apikey.in_([content['APIKEY']]))
    result = query.first()


    #Validate the API-KEY
    #TODO: Make a mapping between APIKEYS and CustomerIDs
    if result:
        if DBG:
            print("APIKEY found")
        # Update CustomerID field
        content['CustomerID'] = result.id
        content['EntryID'] = EntryType['CONTROL']
        
        # Send content to aws controller
        response = aws_controller.db_post(content)
    else:
        response = -1
    
    if response != -1:
        return "SUCCESS"
    else:
        return "FAIL"

if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(host='0.0.0.0')

