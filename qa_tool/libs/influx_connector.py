from pathlib import Path
from influxdb import InfluxDBClient
from qa_tool.libs.reporter import reporter
from qa_tool.utils.utils import generate_date


class InfluxConnector:

    def __init__(self, database=None, host='localhost', user='root', password='root', port=None):
        if ':' in host:
            host, port = host.rsplit(':', 1)
        self.connection = {
            'host': host,
            'port': int(port if port else 8086),
            'username': user,
            'password': password,
            'database': database,
        }
        self.db_conn = InfluxDBClient(host=host, port=port, username=user, password=password, database=database)

    def get_tables_name(self):
        return [i['name'] for i in self.get("SHOW MEASUREMENTS")]

    def get(self, sql, arrg_data=True):
        """
            SQL request can return two series
            if in sql one series, then return list of data
            else {measurement_name1: list_of_data, measurement_name2: list_of_data2}
            :return:
        """
        msg = 'InfluxDB SQL to host: {host}:{port}, db_name: {database}\n{query}'.format(**self.connection, query=sql)
        with reporter.step(msg):
            data = self.db_conn.query(sql)
        if arrg_data:
            if not data.items():
                return []
            return [i for i in data.items()[0][1]]
        else:
            return {table_name[0]: [i for i in generator] for table_name, generator in data.items()}

    def insert_many(self, raw_data):
        return self.db_conn.write_points(raw_data)

    def insert_one(self, measurement, data, time=None):
        data = self.create_row(measurement, data, time)
        return self.db_conn.write_points([data])

    def upload_file(self, file_data):
        if isinstance(file_data, Path):
            file_data = file_data.read_bytes()
        self.db_conn.request(
            'write', 'POST',
            params={'db': self.connection['database']},
            data=file_data,
            headers={'Content-Encoding': 'gzip'},
            expected_response_code=204
        )

    def measurements_format(self, measurements, rp='minute'):
        measurements = measurements if isinstance(measurements, (list, tuple)) else [measurements]
        measurements = [f'"{i}"' if rp is None else f'{rp}."{i}"' for i in measurements]
        return ', '.join(measurements)


if __name__ == "__main__":
    import json
    from settings import INFLUX_CONN_STR, INFLUX_DB

    # kek = InfluxDBClient(host="...", port=80, path="/storage/raw")
    connector = InfluxConnector(INFLUX_DB, host=INFLUX_CONN_STR)
    data = connector.get_tables_name()
    print(data)
    test = connector.get('select * from "okex_ALGO-BTC_ed53ebb83fc84c79b5a80edacce6b01d", "exchange1_M1USD_60" limit 10', arrg_data=False)
    print(test)
