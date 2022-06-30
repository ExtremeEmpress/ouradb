# Docker Image with InfluxDB and Grafana

This Docker image is specifically intended for storing Oura sleep data in an InfluxDB database, and being able to easily do queries from the data using Grafana. It also has a cron job which checks for new data to upload to the database once per hour.

The Docker image is based on original work from [Samuele Bistoletti](https://github.com/samuelebistoletti) in the [Docker Image with Telegraf (StatsD), InfluxDB and Grafana](https://github.com/samuelebistoletti/docker-statsd-influxdb-grafana) and specifically on the improvements made by [Phil Hawthorne](https://github.com/philhawthorne) for persistence in [this Docker Image](https://github.com/philhawthorne/docker-influxdb-grafana).

This repository also contains a python script, which can alone be used for querying data from the Oura API.

## First Step: Get Personal Access Token from Oura

As the very first step, you need to get yourself a Personal Access Token (PAT) from the Oura website, here: https://cloud.ouraring.com/personal-access-tokens

Select "Create New Personal Access Token", and store the token in a safe place. Copy the oura/PAT_empty.txt file to a file named oura/PAT.txt and copy the 32 character long PAT to the new file.

## Second step (optional): Do a test query

To make sure your PAT works, do a test run to get today's sleep data:

```sh
python3 oura/oura_query.py --pat=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

If you don't want to have a database and Grafana, you can just manually browse your data with this script.

Example: Get temperature deviations with 2 decimal accuracy for first week of January 2022 (requires jq):

```sh
user@machine:~/repos/ouradb$ python3 oura/oura_query.py --pat=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX --start=2022-01-01 --end=2022-01-07|jq '.temperature_deviation'
-0.14
-0.1
-0.03
-0.45
-0.13
0
0.15
```

## Third Step: Build and run the docker image

Now you need to build and run the image. When the image runs for the first time, it posts the current day's data to the database.

```sh
docker build -t ouradata .
```

After building, you'll need to run the image. You'll want to build it with persistence, to make sure you don't lose your data. Replace the paths with paths suitable for your environment.

```sh
docker run -d \
  --name docker-ouradb \
  -p 3003:3003 \
  -p 3004:8083 \
  -p 8086:8086 \
  -v /path/for/influxdb:/var/lib/influxdb \
  -v /path/for/grafana:/var/lib/grafana \
  ouradata:latest
```

To stop the container:

```sh
docker stop docker-ouradb
```

To start the container again:

```sh
docker start docker-ouradb
```

## Fourth Step: Post old data to the database

You probably want to have historic data in the database as well. You can do that by providing the start and end dates for the script oura_post_to_influxdb.py.

Example: You got your ring on 1st January 2022. You want to get historic data for the entire January 2022.

```sh
docker exec docker-ouradb python3 /etc/oura/oura_post_to_influxdb.py --start=2022-01-01 --end=2022-01-31
```

## Fifth Step: Create a Grafana dashboard

Next, you want to observe your data in Grafana.

Go to http://localhost:3003 in your browser, and login with username: root, password: root. (Remember to change these!)

You will first need to add InfluxDB as a datasource.

```
1. On the left panel, select the cogwheel ("Configuration") > Data Sources.
2. Select "Add data source".
3. Select InfluxDB.
4. Under "HTTP" > "URL", manually insert "http://localhost:8086". (Even though it looks like it already is there!)
5. Under "InfluxDB Details", set:
  - Database: ouradb
  - User: root
  - Password: root
6. Select "Save & Test".
```

Now, you want to create a dashboard. As an example we will create a dashboard with a panel showing temperatures ("temperature_deviation").

```
1. On the left, select "+" > "Create".
2. Select "Add new panel".
3. At the bottom, in the Query section, select:
  FROM default oura_measurements WHERE
  SELECT field(temperature_deviation) last()
  GROUP BY time($_interval) fill(linear)
4. On the right side, give the Panel a title.
5. On the top right, select "Save". Give your Dashboard a name.
6. To change the amount of days showing on the panel, at the top right you can change the time. Select for example "Last 30 days".
```

Now you are ready to start creating your own panels and exploring your Oura data!
