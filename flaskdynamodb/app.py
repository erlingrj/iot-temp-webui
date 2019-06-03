from quart import Quart, request, render_template, websocket
from aws_controller import DecimalEncoder
import aws_controller
import json
import datetime


DBG = True



app = Quart(__name__)

CURRENT_CUSTOMER = 1
EntryType = {
    'TEMP' : 0,
    'CONTROL' : 1
}

customerApiKey2IdMap = {
    12345:1,
    54321:2
}

@app.route('/')
async def index():
    current_temp = aws_controller.db_get_last_temp()['Data']
    current_control = aws_controller.db_get_last_control()['Data']

    return await render_template('index.html', current_temp=current_temp, current_control=current_control)

@app.route('/stats')
async def stats():
    # Here we will display the historical stuff
    # Maybe make some interesting plots?
    last24, lastw = aws_controller.db_get_stats()
    
    return await render_template('stats.html', data24h=last24, data1w=lastw)

@app.route('/control')
async def new_control_policy():
    # When the user wishes to make a new control policy
    # He will end up in this page
    current_control = list(map(float, aws_controller.db_get_last_control()['Data'].split('-')))
    
    return await render_template('control.html', control_policy = current_control, APIKEY=12345)

@app.route('/about')
async def about():
    return await render_template('about.html')
# This is a websocket to let the Javascript running in the browser
# Communicate with us. When the user has chosen a new Control Policy
# He will press a button that sends it here
@app.websocket('/send-control-policy')
async def send_control_policy():
    while True:
        #TODO: Check validity of data
        data = await websocket.receive()
        t = datetime.datetime.now()
        db_entry = {
            'CustomerID' : CURRENT_CUSTOMER,
            'Timestamp'  : "{}-{}-{}-{}-{}-{}".format(t.day, t.month, t.year, t.hour, t.minute, t.second),
            'EntryID'    : EntryType['CONTROL'],
            'Data'       : data
        }
        aws_controller.db_post(db_entry)
        print("Received data: {}".format(data))






###################################################
#                                                 #
#           API TO THE DATABASE FOR RPI           #
#                                                 #
###################################################

# Dict that maps the API-KEYS to customerIDs
@app.route('/db/get-last-temp', methods=["GET"])
async def get_last_temp():
    return json.dumps(aws_controller.db_get_last_temp(), cls=DecimalEncoder)

@app.route('/db/get-last-control', methods=['GET'])
async def get_last_control():
    return json.dumps(aws_controller.db_get_last_control(), cls=DecimalEncoder)

@app.route('/db/post-temp', methods=['POST'])
async def post_temp():
    content = await request.get_json()
    if DBG:
        print(content)

    #Validate the API-KEY
    #TODO: Make a mapping between APIKEYS and CustomerIDs
    if (content['APIKEY'] in customerApiKey2IdMap):
        if DBG:
            print("APIKEY found")
        # Update CustomerID field
        content['CustomerID'] = customerApiKey2IdMap[content['APIKEY']]
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
async def post_control():
    content = await request.get_json()
    if DBG:
        print(content)

    #Validate the API-KEY
    #TODO: Make a mapping between APIKEYS and CustomerIDs
    if (content['APIKEY'] in customerApiKey2IdMap):
        if DBG:
            print("APIKEY found")
        # Update CustomerID field
        content['CustomerID'] = customerApiKey2IdMap[content['APIKEY']]
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
    app.run()

