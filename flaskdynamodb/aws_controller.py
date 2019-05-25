import boto3
import json
import decimal
import datetime
from boto3.dynamodb.conditions import Key, Attr

DBG = True

db = boto3.resource('dynamodb')
DB_NAME = 'TempTable'
CUSTOMER_ID = 1


# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


def db_get_last_temp():
    table = db.Table(DB_NAME)
    response = table.query(
        KeyConditionExpression = Key('CustomerID').eq(CUSTOMER_ID),
        ScanIndexForward = False,
        FilterExpression=Attr('EntryID').eq(0)
    )
    if response['Count'] > 0:
        return response['Items'][0]
    else:
        return 0



def db_get_last_control():
    # Return the last control entry from the DB
    table = db.Table(DB_NAME)
    response = table.query(
        KeyConditionExpression = Key('CustomerID').eq(CUSTOMER_ID), #Check only for our guy
        ScanIndexForward = False, #Backwards so we start from the last
        FilterExpression=Attr('EntryID').eq(1) #Check for EntryID = 1 that is a Control Event
    )
    if response['Count'] > 0:
        return response['Items'][0]
    else:
        return 0

def db_post(content):
    table = db.Table(DB_NAME)
    if DBG:
        print(content)
    try:
        table.put_item(
            Item={
                'CustomerID' : content['CustomerID'],
                'Timestamp'  : content['Timestamp'],
                'EntryID'    : content['EntryID'],
                'Data'       : content['Data']
            }
        )
        return 1
    except:
        return -1

# The following functions are for getting the stats out of the DB
# They are hardcoded for retrieving exactly what we want

def db_get_stats():
    table = db.Table(DB_NAME)
    response = table.query(
        KeyConditionExpression = Key('CustomerID').eq(CUSTOMER_ID),
        ScanIndexForward = False,
        FilterExpression=Attr('EntryID').eq(0)
    )
    if response['Count'] > 0:
        data24h = db_get_24h(response)
        print(data24h)
        #data1w = db_get1w(response)
    else:
        print("ERROR IN DB_GET_STATS()")

def db_get_24h(response):
    n_hours = 24
    now = datetime.datetime.now()
    h = datetime.timedelta(hours=1)
    now = now.replace(minute = 0, second=0)
    labels = [now]
    values = [None] * 24
    # Construct the labels as datetime objects
    for i in range(0,24):
        now -= h
        labels.append(now)
    
    running_vals = []
    label_i = 0 # Iterator through the labels
    # Now lookup last 
    for e in response['Items']:
        print(e)
        ts = list(map(int, e['Timestamp'].split('-'))) #Extract timestamp and convert it to int
        d= datetime.datetime(ts[2],ts[1],ts[0],ts[3],ts[4]) #Construct a datetime object of current entry
        if d>labels[label_i+1]: # If this entry belongs to label_i
            running_vals.append(float(e['Data']))
        else: # We have to move down the label list
            print("Next label")
            print(running_vals)
            if len(running_vals) > 0:
                values[label_i] = sum(running_vals)/len(running_vals)
                running_vals = []
            label_i += 1
            if label_i >= 24:
                break

    str_labels = [label.strftime("%a %H:%m") for label in labels]

    return (str_labels, values)


def db_get_1w():
    print("TO BE IMPLEMENTED")