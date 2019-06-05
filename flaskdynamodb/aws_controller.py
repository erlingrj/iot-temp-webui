import boto3
import json
import decimal
import datetime
import dateutil.parser
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


def db_get_last_temp(customerID):
    table = db.Table(DB_NAME)
    response = table.query(
        KeyConditionExpression = Key('CustomerID').eq(customerID),
        ScanIndexForward = False,
        FilterExpression=Attr('EntryID').eq(0)
    )
    if response['Count'] > 0:
        return response['Items'][0]
    else:
        return None



def db_get_last_control(customerID):
    # Return the last control entry from the DB
    table = db.Table(DB_NAME)
    response = table.query(
        KeyConditionExpression = Key('CustomerID').eq(customerID), #Check only for our guy
        ScanIndexForward = False, #Backwards so we start from the last
        FilterExpression=Attr('EntryID').eq(1) #Check for EntryID = 1 that is a Control Event
    )
    if response['Count'] > 0:
        return response['Items'][0]
    else:
        return None

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

def db_get_stats(customerID):
    table = db.Table(DB_NAME)

    data24h = db_get_24h(table, customerID)
    data1w = db_get_1w(table, customerID)
    return (data24h, data1w)
    


def db_get_temp_from_dates(table,dates,customerID):
    values = [None] * (len(dates)-1)
    for i in range(0, len(dates)-1):
        response = table.query(
            KeyConditionExpression = Key('CustomerID').eq(customerID) & Key('Timestamp').between(dates[i].isoformat(), dates[i+1].isoformat()),
            ScanIndexForward = False,
            FilterExpression=Attr('EntryID').eq(0)
        )
        n_vals = 0
        tot = 0
        for entry in response['Items']:
            tot += float(entry['Data'])
            n_vals += 1
        
        if n_vals>0:
            values[i] = tot/n_vals
    
    return values
        



def db_get_24h(table,customerID):
    n_hours = 24
    now = datetime.datetime.now()
    h = datetime.timedelta(hours=1)
    now_rounded = now.replace(minute = 0, second=0, microsecond=0)
    dates = []
    # Construct the labels as datetime objects
    for i in range(24,-1,-1):
        dates.append(now_rounded - i*h)
    dates.append(now.replace(microsecond = 0))
    
    values = db_get_temp_from_dates(table, dates, customerID)
    
    #Generate the strings for the plotting
    str_labels = [date.strftime("%a %H:%M") for date in dates[0:-1]]

    return (str_labels, values)

def db_get_1w(table, customerID):
    n_datapoints = 28
    res = 6
    now = datetime.datetime.now().replace(microsecond=0)
    now_rounded = now.replace(minute = 0, second = 0)
    h = datetime.timedelta(hours = res)

    dates = []
    values = [None] * 24
    # Construct the labels as datetime objects
    for i in range(24,-1,-1):
        dates.append(now_rounded - i*h)
    
    dates.append(now)
    values = db_get_temp_from_dates(table,dates,customerID)

   

    str_labels = [date.strftime("%a %H:%M") for date in dates[0:-1]]

    return (str_labels, values)