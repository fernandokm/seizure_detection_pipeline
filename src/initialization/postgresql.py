from cmath import isinf
import psycopg2
import csv
from datetime import datetime


def push_postgresql_data(
    data: dict, host: str, database: str, username: str, password: str, port: int = 5432
):
    """
    Push data to postgresql
    data: input data {
        table_name: [{column1: value1, column2: value2}, {column1: value1, column2: value2},...]
    }
    """
    conn = psycopg2.connect(
        host=host, database=database, user=username, password=password, port=port
    )
    try:
        with conn.cursor() as curs:
            for table, content in data.items():
                generate_table(curs, table, content)
                conn.commit()
    except Exception as e:
        conn.rollback()
        print(e)
    finally:
        conn.close()


def generate_table(cursor, table, content):
    """
    Create table in postgresql & fill it
    cursor: cursor
    table: table name
    content: table content
    """
    cursor.execute(f"DROP TABLE IF EXISTS {table}")
    first_row: list = content[0]

    def type_maping(item):
        column, value = item
        if type(value) == str:
            return f"{column} varchar(255)"
        elif isinstance(value, datetime):
            return f"{column} timestamp"
        elif isinstance(value, float):
            return f"{column} real"
        else:
            return f"{column} integer"

    columns_sql = ", ".join((map(type_maping, first_row.items())))
    cursor.execute(f"CREATE TABLE {table} ({columns_sql})")
    fill_table(cursor, table, content)


def fill_table(cursor, table, content):
    """
    Fills existing table in postgresql with content
    cursor: cursor
    table: table name
    content: table content
    """
    for row in content:
        columns_sql = ", ".join((map(lambda column: f"{column}", row.keys())))
        values_sql = ", ".join(
            (
                map(
                    lambda column: f"'{row[column]}'"
                    if type(row[column] == "str")
                    else f"{row[column]}",
                    row.keys(),
                )
            )
        )
        cursor.execute(f"INSERT INTO {table} ({columns_sql}) VALUES ({values_sql})")


def get_data_from_csv(filepath):
    """
    Transforms data from csv to list of dicts for each line
    """
    with open(filepath, "r") as csv_file:
        return csv.DictReader(csv_file)


def get_data_from_csv_dict(csv_files):
    """
    Transforms data from dict of csv files (table name: csv filepath) to push_postgresql data format
    """
    data = {}
    for table, filepath in csv_files.items():
        data[table] = get_data_from_csv(filepath)
    return data


if __name__ == "__main__":

    def string_to_date(string):
        return datetime.strptime(string, "%Y-%m-%d %H:%M:%S")

    # data = {"my_test_table_2": [{"time": string_to_date("2022-01-18 06:03:41"), "letter": "A", "number": 2.0}, {"time": string_to_date("2022-01-18 07:03:41"), "letter": "B", "number": -4.3}, {
    #     "time": string_to_date("2022-01-18 08:03:41"), "letter": "C", "number": 5.1}, {"time": string_to_date("2022-01-18 09:03:41"), "letter": "D", "number": 0.0}, {"time": string_to_date("2022-01-18 10:03:41"), "letter": "E", "number": 1.2}]}
    # push_postgresql_data(data, "localhost", "grafana",
    #                      "postgres", "wdkjsdk8hcjbw")
    data = {
        "my_test_table_2": [
            {
                "time": string_to_date("2022-01-18 06:03:41"),
                "letter": "sdnn > 45.06",
                "number": 0.047,
            },
            {
                "time": string_to_date("2022-01-18 07:03:41"),
                "letter": "38.08 < rmssd <= 47.95",
                "number": -0.0125,
            },
            {
                "time": string_to_date("2022-01-18 08:03:41"),
                "letter": "median_nni > 710.00",
                "number": 0.011,
            },
            {
                "time": string_to_date("2022-01-18 09:03:41"),
                "letter": "0.05 < cvsd <= 0.06",
                "number": -0.009,
            },
            {
                "time": string_to_date("2022-01-18 10:03:41"),
                "letter": "1.00 < nni_50 <= 3.00",
                "number": -0.006,
            },
            {
                "time": string_to_date("2022-01-18 10:03:41"),
                "letter": "lf > 808.47",
                "number": 0.008,
            },
        ]
    }
    push_postgresql_data(data, "localhost", "grafana", "postgres", "wdkjsdk8hcjbw")
