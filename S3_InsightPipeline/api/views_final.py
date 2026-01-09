# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import json
import boto3
import datetime
import mysql.connector
import urllib.request

# SECURITY: Use environment variables instead of hardcoding credentials
import os
hostname = os.getenv('RDS_HOSTNAME', 'your-rds-endpoint.rds.amazonaws.com')
username = os.getenv('RDS_USERNAME', 'admin')
password = os.getenv('RDS_PASSWORD', '')  # Set via environment variable
database = os.getenv('RDS_DATABASE', 'invoicedb')

s3_target_bucket = os.getenv('S3_TARGET_BUCKET', 'your-target-bucket-name')

@csrf_exempt
def message(request):
    print('*********************** Incoming request *****************************')
    print_request(request)

    # Parse the SNS message
    try:
        sns_message = json.loads(request.body)
        message_type = sns_message.get('Type')

        # Handle SNS subscription confirmation
        if message_type == 'SubscriptionConfirmation':
            subscribe_url = sns_message.get('SubscribeURL')
            print(f'Confirming SNS subscription: {subscribe_url}')
            # Visit the URL to confirm subscription
            with urllib.request.urlopen(subscribe_url) as response:
                print(f'Subscription confirmed! Response: {response.status}')
            return HttpResponse('SNS Subscription confirmed successfully')

        # Handle SNS notification (the actual S3 event)
        elif message_type == 'Notification':
            process_document(request.body)
            return HttpResponse('API invoked; your http record is now saved.')

        else:
            print(f'Unknown message type: {message_type}')
            return HttpResponse('Unknown message type')

    except Exception as e:
        print(f'Error processing request: {e}')
        return HttpResponse(f'Error: {e}', status=500)

def print_request(request):
    headers = ''
    for header, value in request.META.items():
        if not header.startswith('HTTP'):
            print('  Req meta item:', header, value)
            continue
        header = '-'.join([h.capitalize() for h in header[5:].lower().split('_')])
        headers += '{}: {}\n'.format(header, value)
    req_header = (
        '{method} HTTP/1.1\n'
        'Content-Length: {content_length}\n'
        'Content-Type: {content_type}\n'
        'Headers: {headers}\n'
        'Body: {body}'
    ).format(
        method=request.method,
        content_length=request.META.get('CONTENT_LENGTH', ''),
        content_type=request.META.get('CONTENT_TYPE', ''),
        headers=headers,
        body=request.body,
    )
    print(req_header)
    if request.method == 'GET':
        print('Request method = GET')
        for key, value in request.GET.lists():
            print("Key=%s\nValue=%s" % (key, value))
    elif request.method == 'POST':
        print('Request method = POST')
        for key, value in request.POST.lists():
            print("Key=%s\nValue=%s" % (key, value))

def process_document(s3json):
    print('The S3 JSON is:', s3json)
    nmsgjson = json.loads(s3json)
    s3 = json.loads(nmsgjson['Message'])
    if 'Records' not in s3:
        return
    bucket = s3['Records'][0]['s3']['bucket']['name']
    filename = s3['Records'][0]['s3']['object']['key']
    print('Will read the file %s from the bucket %s' % (filename, bucket))
    s3 = boto3.resource('s3')
    obj = s3.Object(bucket, filename)
    content = obj.get()['Body'].read().decode('utf-8').replace(",", ";")
    create_table()
    cust_id = 'def'
    inv_id = 'def_001'
    line = ''
    for one_char in content:
        if one_char == '\n':
            print('Line->', line)
            if "Customer-ID:" in line:
                cust_id = line.split()[1]
                print('  Found Customer-ID', cust_id)
            elif "Inv-ID:" in line:
                inv_id = line.split()[1]
                print('  Found Invoice-ID', inv_id)
            line = ''
            insert_data(cust_id, inv_id)
        else:
            line += one_char
    xform_content = transform_content(cust_id, inv_id, content)
    print('CSV ->', xform_content)
    write_to_target_bucket(cust_id, inv_id, content, xform_content)

def create_table():
    print('\n*************************************************************************')
    print('Creating table invoice')
    conn = mysql.connector.connect(host=hostname, user=username, passwd=password, db=database)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS invoice (cust_id VARCHAR(255), inv_id VARCHAR(255))")
    cur.close()
    conn.close()

def insert_data(cust_id, inv_id):
    print('\n*************************************************************************')
    print('Inserting data into invoice table')
    conn = mysql.connector.connect(host=hostname, user=username, passwd=password, db=database)
    cur = conn.cursor()
    cur.execute("INSERT INTO invoice (cust_id, inv_id) VALUES (%s, %s)", (cust_id, inv_id))
    conn.commit()
    cur.close()
    conn.close()

def write_to_target_bucket(cust_id, inv_id, content, xform_content):
    now = datetime.datetime.now()
    prefix_val = str(now.microsecond) + str(now.second)
    object_key = prefix_val + '_' + cust_id + '_' + inv_id + '.csv'
    print("Written new s3 file", object_key)
    print("Uploading S3 object content", xform_content)
    s3 = boto3.client('s3')
    s3.put_object(Bucket=s3_target_bucket, Key=object_key, Body=xform_content.encode())
    print("Done")

def transform_content(cust_id, inv_id, content):
    line = ''
    dated = ''
    fromcust = ''
    tocust = ''
    amt = ''
    sgst = ''
    tot = ''
    words = ''
    for one_char in content:
        if one_char == '\n':
            if "Dated:" in line:
                dated = line.split(":")[1]
                print('  Found dated', dated)
            elif "From:" in line:
                fromcust = line.split(":")[1]
                print('  Found fromcust', fromcust)
            elif "To:" in line:
                tocust = line.split(":")[1]
                print('  Found tocust', tocust)
            elif "Amount:" in line:
                amt = line.split(":")[1]
                print('  Found amt', amt)
            elif "SGST:" in line:
                sgst = line.split(":")[1]
                print('  Found sgst', sgst)
            elif "Total:" in line:
                tot = line.split(":")[1]
                print('  Found tot', tot)
            elif "InWords:" in line:
                words = line.split(":")[1]
                print('  Found words', words)
            line = ''
        else:
            line += one_char
    return cust_id + "," + inv_id + "," + dated + "," + fromcust + "," + tocust + "," + amt + "," + sgst + "," + tot + "," + words
