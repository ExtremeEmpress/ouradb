from datetime import datetime, timedelta
import influxdb_client, os, time
from influxdb_client import WritePrecision, InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import requests
import argparse
import json
import re

#Influxdb2 info
INFLUXDB_TOKEN = open('/etc/oura/INFLUXDBTOKEN.txt','r').read(88)
org = "my-org"
bucket ="my-bucket"
url = "http://2.2.2.3:8086"
client_ouradb = influxdb_client.InfluxDBClient(url=url, token=INFLUXDB_TOKEN, org=org)
write_api = client_ouradb.write_api(write_options=SYNCHRONOUS)

pat = open('/etc/oura/PAT.txt','r').read(32)


def fetch_data(start, end, datatype, pat_data):
    url = f"https://api.ouraring.com/v2/usercollection/{datatype}"
    headers = {"Authorization": f"Bearer {pat_data}"}
    params = {"start_date": f"{start.strftime('%Y-%m-%d')}", 'end_date': f"{end.strftime('%Y-%m-%d')}"}
    response = requests.request('GET', url, headers=headers, params=params).json()

    if not response["data"]:
        print("No {} data yet for time window, exiting".format(datatype))
        exit()

    resp = response["data"][0]

    #If we're looking for sleep...cycles through the items in response dictionary, finds the one that contains long_sleep, sets the active resp to that section. Otherwise naps make amess of the data.
    indexstart = 0
    indexceiling = len(response["data"]) - 1 
    if datatype == 'sleep':
        while indexstart <= indexceiling:
            resp2 = response["data"][indexstart]
            for k, v in resp2.items():
                if v == "long_sleep":
                    resp = resp2
            indexstart+= 1
    
    #Adds the contributors section at level 0 of our readiness json. Includes stats like hrv and sleep balance
    if datatype == 'daily_readiness':
        resp2 = response["data"][0]["contributors"]
        resp.pop('contributors', None)
        resp.update(resp2)
        
    # All data should be consistent in influxdb, so turn ints to floats
    resp = {k:float(v) if type(v) == int else v for k,v in resp.items()}
    return resp

def get_data_one_day(date,pat):
    end_date=datetime.strptime(date,'%Y-%m-%d')
    start_date=end_date - timedelta(days=1)
    

    sleep_data = fetch_data(start_date,end_date,'sleep',pat)
    readiness_data = fetch_data(start_date,end_date,'daily_readiness',pat)
 
    if sleep_data == None:
        print("No data, exiting")
        exit()


    # Clean out array type data
    sleep_data.pop('heart_rate', None)
    sleep_data.pop('hrv', None)
    sleep_data.pop('movement_30_sec', None)
    sleep_data.pop('sleep_phase_5_min', None)
    sleep_data.pop('low_battery_alert', None)
    sleep_data.pop('type', None)
    sleep_data.pop('readiness', None)
    readiness_data.pop('contributors', None)
    
 



    # Merge sleep and readiness data
    data = sleep_data
    data.update(readiness_data)

    post_data = [{"measurement": "oura_measurements",
             "time": data['bedtime_end'],
             "fields": data
    },]
    
    return post_data


parser = argparse.ArgumentParser(description='Post Oura data to Influxdb. Omit --start and --end to process data only for today.')
parser.add_argument('--start', help="Start date of query. Format: YYYY-MM-DD")
parser.add_argument('--end', help="End date of query. Format: YYYY-MM-DD")
args = parser.parse_args()

if (args.end and not args.start) or (args.start and not args.end):
    print("Provide both --start and --end dates. Omit both to process data for today.")
    exit()

date_pattern = re.compile("^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
    
if args.start:
    if not date_pattern.match(args.start):
        print("Start date format invalid. Use format: YYYY-MM-DD")
        exit()

if args.end:
    if not date_pattern.match(args.end):
        print("End date format invalid. Use format: YYYY-MM-DD")
        exit()

only_today = False

if not args.start and not args.end:
    start_date = datetime.now()
    end_date = start_date + timedelta(days=1)
    only_today = True
else:
    start_date = datetime.strptime(args.start,'%Y-%m-%d') + timedelta(days=1)
    end_date = datetime.strptime(args.end,'%Y-%m-%d') + timedelta(days=1)


# Go through all days between start and end dates

while start_date <= end_date:
    data = get_data_one_day(end_date.strftime('%Y-%m-%d'),pat)
    write_api.write(bucket=bucket, org=org, record=data)
    print(end_date)
    #print(json.dumps(data, indent=4))
    end_date = end_date - timedelta(days=1)

