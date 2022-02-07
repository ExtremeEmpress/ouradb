from datetime import datetime, timedelta
import requests
import argparse
import json
import re



def fetch_data(start, end, datatype, pat_data):
    path = "https://api.ouraring.com/v1/{}?start={}&end={}".format(datatype, start.strftime('%Y-%m-%d'),end.strftime('%Y-%m-%d'))
    header = {"Authorization": "Bearer {}".format(pat_data)}

    response = requests.get(path,headers=header).json()

    if not response[datatype]:
        print("No {} data yet for time window, exiting".format(datatype))
        exit()

    resp = response[datatype][0]

    # All data should be consistent in influxdb, so turn ints to floats
    resp = {k:float(v) if type(v) == int else v for k,v in resp.items()}
    return resp

def main():

    parser = argparse.ArgumentParser(description='Fetch Oura data from cloud. Omit --start and --end to fetch data only for today. Returns data in JSON format.')
    parser.add_argument('--pat', help="Personal Access Token. Required. Get yours from https://cloud.ouraring.com/personal-access-tokens")
    parser.add_argument('--start', help="Start date of query. Format: YYYY-MM-DD")
    parser.add_argument('--end', help="End date of query. Format: YYYY-MM-DD")
    parser.add_argument('--datatype', default="sleep", help="Type of data to query. Values: sleep, readiness, activity. Defaults to sleep.")
    args = parser.parse_args()

    if (args.end and not args.start) or (args.start and not args.end):
        print("Provide both --start and --end dates. Omit both to get data for today.")
        exit()

    date_pattern = re.compile("^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
    datatype_pattern = re.compile("^(sleep|readiness|activity)$")
    pat_pattern = re.compile("^[A-Z0-9]{32}$")
    
    if args.start:
        if not date_pattern.match(args.start):
            print("Start date format invalid. Use format: YYYY-MM-DD")
            exit()

    if args.end:
        if not date_pattern.match(args.end):
            print("End date format invalid. Use format: YYYY-MM-DD")
            exit()

    if not args.start and not args.end:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
    else:
        start_date = datetime.strptime(args.start,'%Y-%m-%d')
        end_date = datetime.strptime(args.end,'%Y-%m-%d')

    if args.datatype:
        if not datatype_pattern.match(args.datatype):
            print("Datatype format invalid. Available values: sleep, readiness, activity. Omit to get only sleep data.")
            exit()

    if not args.pat:
        print("PAT required. Get yours from https://cloud.ouraring.com/personal-access-tokens")
        exit()
    else:
        if not pat_pattern.match(args.pat):
            print("PAT fromat invalid. Should be a 32 character string.")
            exit()

    datatype = args.datatype
    
    pat = args.pat

    while start_date <= end_date:
        tmp_date = end_date - timedelta(days=1)
        data = fetch_data(tmp_date,end_date,datatype,pat)
        print(json.dumps(data))
        end_date = tmp_date
    
if __name__ == "__main__":
    main()
