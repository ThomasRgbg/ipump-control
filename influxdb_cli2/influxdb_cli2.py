import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS

from datetime import datetime, timedelta, timezone

class influxdb_cli2:
    def __init__(self, influxdb_url, token, org, bucket, debug = False):
        self.influxdb_client = influxdb_client.InfluxDBClient(url=influxdb_url, token=token, org=org)
        self.bucket=bucket
        self.org = org
        self.debug = debug

        self.write_api = self.influxdb_client.write_api(write_option=SYNCHRONOUS)

    def write_sensordata(self, location, measurement, value, timestamp = None, force = None):
        if value == None:
            return
        if timestamp == None:
            timestamp = datetime.utcnow()

        if self.debug:
            print("Got sample: location: {0}, measurement: {1}, value {2}, timestamp {3}".format(location,measurement,value, timestamp))

        if force == None:
            if float(value) == 0.0:
                if self.debug:
                    print("discarding value, since zero")
                return

        write_data = [
            {
                'measurement': measurement,
                'tags': {
                    'location': location
                },
                'fields': {
                    'value': float(value)
                },
                'time' : timestamp.isoformat()
            }
        ]
        if self.debug:
            print("write to influxdb: {0}".format(write_data))
        self.write_api.write(self.bucket, self.org , write_data)


    # working query
    # from(bucket: "pentling/autogen")
    #  |> range(start: v.timeRangeStart, stop:v.timeRangeStop)
    #  |> filter(fn: (r) => r._measurement == "Battery_Power" and r.location == "pv_fronius")

    def query_data(self, location, measurement, start_date, end_date):
        start_date = start_date.isoformat(sep='T', timespec='seconds')
        end_date = end_date.isoformat(sep='T', timespec='seconds')
        query_api = self.influxdb_client.query_api()
        query = 'from(bucket: "{0}")\
        |> range(start: {1}Z, stop: {2}Z)\
        |> filter(fn:(r) => r._measurement == "{3}")\
        |> filter(fn:(r) => r.location == "{4}")'.format(self.bucket,start_date,end_date,measurement,location)
        if self.debug:
            print("Query: {0}".format(query))
        result = query_api.query(query=query)
        result = result.to_values(columns=['_time', 'location', '_measurement', '_value' ])
        if self.debug:
            print("Result: {0}".format(result))
        return result

