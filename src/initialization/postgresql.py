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

    import pandas as pd

    shap_data = pd.read_csv("df_grafana_1.csv")[
        [
            "shap_values_mean_nni",
            "mean_nni",
            "shap_values_sdnn",
            "sdnn",
            "lf_hf_ratio",
            "sdsd",
            "shap_values_sdsd",
            "interval_start_time",
            "shap_values_interval_start_time",
            "cvi",
        ]
    ]
    shap_data_list = shap_data.to_dict(orient="records")
    push_postgresql_data(
        {"shap_data": shap_data_list},
        "localhost",
        "grafana",
        "postgres",
        "wdkjsdk8hcjbw",
    )
