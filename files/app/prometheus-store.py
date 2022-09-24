"""Application exporter"""

from influxdb_client import InfluxDBClient
import os
import time
from prometheus_client import start_http_server, Gauge, Enum, Info
import logging
import requests

LOG_LEVEL = os.getenv("LOG_LEVEL", "WARN")

PROMETHEUS_PREFIX = os.getenv("PROMETHEUS_PREFIX", "store")
PROMETHEUS_PORT   = int(os.getenv("PROMETHEUS_PORT", "9011"))

influx_org = os.getenv("influx_org", "prometheus")
influx_bucket = os.getenv("influx_bucket", "prometheus")
influx_token = os.getenv("influx_token", "")
influx_client = os.getenv("influx_client", "http://localhost:9999")

polling_interval_seconds = int(os.getenv("POLLING_INTERVAL_SECONDS", "60"))

LOGFORMAT = '%(asctime)-15s %(message)s'

logging.basicConfig(level=LOG_LEVEL, format=LOGFORMAT)
LOG = logging.getLogger("prometheus-store")

class AppMetrics:
    """
    Representation of Prometheus metrics and loop to fetch and transform
    application metrics into Prometheus metrics.
    """

    def __init__(self, PROMETHEUS_PREFIX="", PROMETHEUS_PORT="", influx_token="", influx_org="", influx_bucket="", influx_client="", polling_interval_seconds=5):

        if PROMETHEUS_PREFIX != '':
            PROMETHEUS_PREFIX = PROMETHEUS_PREFIX + "_"

        self.PROMETHEUS_PREFIX = PROMETHEUS_PREFIX
        self.PROMETHEUS_PORT = PROMETHEUS_PORT
        self.influx_token = influx_token
        self.influx_org = influx_org
        self.influx_bucket = influx_bucket
        self.influx_client = influx_client
        self.influx_client = influx_client
        self.polling_interval_seconds = polling_interval_seconds

        self.status = Info(PROMETHEUS_PREFIX + 'status', 'status')
        self.datasizing = Gauge(PROMETHEUS_PREFIX + 'datasizing', 'datasizing')

    def run_metrics_loop(self):
        """Metrics fetching loop"""

        while True:
            self.fetch()
            time.sleep(self.polling_interval_seconds)

    def fetch(self):
        """
        Get metrics from application and refresh Prometheus metrics with
        new values.
        """

        count = 0

        query = 'from(bucket: "'+ influx_bucket + '")\
        |> range(start: -10m)\
        |> filter(fn: (r) => r._measurement == "h2o_level")\
        |> filter(fn: (r) => r._field == "water_level")\
        |> filter(fn: (r) => r.location == "coyote_creek")'

        #establish a connection
        client = InfluxDBClient(url=influx_client, token=influx_token, org=influx_org)

        #instantiate the WriteAPI and QueryAPI
        write_api = client.write_api()
        query_api = client.query_api()

        #create and write the point
        p = Point("h2o_level").tag("location", "coyote_creek").field("water_level", 1)
        write_api.write(bucket=influx_bucket,org=influx_org,record=p)
        #return the table and print the result
        result = client.query_api().query(org=influx_org, query=query)
        results = []
        for table in result:
            for record in table.records:
                results.append((record.get_value(), record.get_field()))
                count+=1

        self.datasizing.set( count )
        LOG.info( count )

def main():
    if influx_token != "":
        app_metrics = AppMetrics(
            PROMETHEUS_PREFIX=PROMETHEUS_PREFIX,
            PROMETHEUS_PORT=PROMETHEUS_PORT,
            influx_token=influx_token,
            influx_org=influx_org,
            influx_bucket=influx_bucket,
            influx_client=influx_client,
            polling_interval_seconds=polling_interval_seconds
        )
        start_http_server(PROMETHEUS_PORT)
        LOG.info("start prometheus port: %s", PROMETHEUS_PORT)
        app_metrics.run_metrics_loop()
    else:
        LOG.error("APIKEY is invalid")

if __name__ == "__main__":
    main()
