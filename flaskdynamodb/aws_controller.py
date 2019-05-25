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
        data24h = db_get24h(response)
        #data1w = db_get1w(response)
    else:
        print("ERROR IN DB_GET_STATS()")

def db_get_24h():
    now = datetime.datetime.now()
    h = datetime.timedelta(hours=2)
    now.minute = 0
    now.second = 0
    labels = [now]
    # Construct the labels as datetime objects
    for (i in range(0,11)):
        now -= h
        labels.append(now)
    
    # Now lookup last 
    for e in response['Items']:
        

        



def db_get_1w():