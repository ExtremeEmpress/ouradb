from datetime import datetime, timedelta
from influxdb import InfluxDBClient
import requests
import argparse
import json
import re
import oura_query

def get_data_one_day(date,pat):
    end_date=datetime.strptime(date,'%Y-%m-%d')
    start_date=end_date - timedelta(days=1)
    

    sleep_data = oura_query.fetch_data(start_date,end_date,'sleep',pat)
    readiness_data = oura_query.fetch_data(start_date,end_date,'daily_readiness',pat)
 
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
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)
    only_today = True
else:
    start_date = datetime.strptime(args.start,'%Y-%m-%d')
    end_date = datetime.strptime(args.end,'%Y-%m-%d')

   
pat = open("/etc/oura/PAT.txt","r").read(32)

client_ouradb = InfluxDBClient(host="localhost", port=8086, database="ouradb")

# If you wish to reduce queries to the Oura API, you can uncomment the following steps.
# This way no more queries are done after data has already been received that day.
# Note that if you wake up early, look at the Oura app, and then sleep more, uncommenting
# the following rows will cause that any updated data is not posted to the database from that day.

#if only_today:
#    a = client_ouradb.query("Select * from oura_measurements where bedtime_end =~ /{}/".format(end_date.strftime('%Y-%m-%d')))
#    if a:
#        print("Data for today already exists in DB")
#        exit()



# Go through all days between start and end dates

while start_date <= end_date:
    data = get_data_one_day(end_date.strftime('%Y-%m-%d'),pat)
    client_ouradb.write_points(data)
    #print(end_date)
    #print(json.dumps(data, indent=4))
    end_date = end_date - timedelta(days=1)

