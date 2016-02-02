from __future__ import print_function
import time
import boto3
import os
import datetime
from decimal import Decimal
import json

#####
# AWS Lambda function which receives data from IoT and puts them to DynamoDB and S3.
#
# Author: Arik Guggenheim (arik.guggenheim@arik.sydney)
# Date: 26.01.2016
#####

print('Loading function')

def insert_to_dynamo(event):
    dynamodb = boto3.resource('dynamodb')
    lwfmeteoTable = dynamodb.Table('table name')
    lwfmeteoTable.put_item(
        Item={
            "site": "RPI",
            "timestamp": Decimal(str(event['timestamp'])),
            "temp": Decimal(str(event['temp'])),
            "rH": Decimal(str(event['rH'])),
            "press": Decimal(str(event['press']))
        }
    )

def download_file():
    try:
        s3 = boto3.resource('s3')
        s3.meta.client.download_file('S3 bucket', 'path/sensorPi.json', '/tmp/sensorPi.json')
    except Exception as e:
        with open(('/tmp/sensorPi.json'), 'w') as f:
             f.close()

def upload_file():
    s3 = boto3.resource('s3')
    s3.meta.client.upload_file('/tmp/sensorPi.json', 'S3 bucket', 'path/sensorPi.json', {'ACL': 'public-read', 'ContentType': 'application/json'})

def get_last_timestamp(actual_ts):
    t = datetime.datetime.fromtimestamp(actual_ts) - datetime.timedelta(days=3)
    return int(time.mktime(t.timetuple()))

def is_file_empty(fpath):
    return True if os.path.isfile(fpath) and os.path.getsize(fpath) > 0 else False

def get_json():
    last_ts = get_last_timestamp(int(time.time()))
    data2 = []
    with open(('/tmp/sensorPi.json'), 'r') as f:
        if not is_file_empty('/tmp/sensorPi.json'):
            return data2
        data = json.load(f)
    for ele in data:
        if ele['timestamp'] > last_ts:
            data2.append(ele)
    return data2

def add_new_events(event, json_data):
    #AmCharts needs js timestamp, so we multiply it with 1000
    event['timestamp'] = event['timestamp'] * 1000
    json_data.append(event)
    return json_data

def write_new_file(new_data):
    with open(('/tmp/sensorPi.json'), 'w') as f:
        json.dump(new_data, f, ensure_ascii=False)
        f.close()


def lambda_handler(event, context):
    insert_to_dynamo(event)
    download_file()
    new_data = add_new_events(event, get_json())
    write_new_file(new_data)
    upload_file()