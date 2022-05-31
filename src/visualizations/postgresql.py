import psycopg2
import csv
from datetime import datetime
import pandas as pd

from typing import Generator


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
    cursor.execute(f"DROP TABLE IF EXISTS \"{table}\"")
    sql_columns_list = format_sql_columns(content)
    if sql_columns_list is not None : 
        columns_sql = ", ".join(sql_columns_list)
        cursor.execute(f"CREATE TABLE \"{table}\" ({columns_sql})")
        fill_table(cursor, table, content)


def format_sql_columns(l):
    """
    Returns the list of columns postgresql types
    l - list of dicts
    return: list of postgresql types
    """
    if len(l) > 0 : 
        columns = l[0].keys()
        nb_rows = len(l)
        return_list = []
        for column in columns:
            i = 0
            while i < nb_rows - 1 or l[i][column] == float("NaN"):
                i += 1
            if i >= nb_rows:
                return_list.append(f"{column} varchar(255)")
            elif isinstance(l[i][column], datetime):
                return_list.append(f"{column} timestamp")
            elif isinstance(l[i][column], float):
                return_list.append(f"{column} double precision")
            elif isinstance(l[i][column], int):
                return_list.append(f"{column} integer")
            else:
                return_list.append(f"{column} varchar(255)")
        return return_list


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
        cursor.execute(f"INSERT INTO \"{table}\" ({columns_sql}) VALUES ({values_sql})")


def get_data_from_csv(filepath):
    """
    Transforms data from csv to list of dicts for each line
    """
    df = pd.read_csv(filepath)
    return df.to_dict(orient="records")


def get_data_from_csv_dict(csv_files):
    """
    Transforms data from dict of csv files (table name: csv filepath) to push_postgresql data format
    """
    data = {}
    for table, filepath in csv_files.items():


        data[table] = get_data_from_csv(filepath)
    return data


def push_postgresql_data_from_pd_dataframe(
    df: pd.DataFrame,
    host: str,
    database: str,
    username: str,
    password: str,
    table_name: str,
    port: int = 5432,
):
    """
    Push data to postgresql
    df: input data {
        table_name: [{column1: value1, column2: value2}, {column1: value1, column2: value2},...]
    }
    """
    data = df.to_dict(orient="records")
    push_postgresql_data({table_name: data}, host, database, username, password, port)


def query(
    host: str,
    database: str,
    username: str,
    password: str,
    query: str,
    port: int = 5432,
):
    """
    Query postgresql
    """
    conn = psycopg2.connect(
        host=host, database=database, user=username, password=password, port=port
    )
    try:
        with conn.cursor() as curs:
            curs.execute(query)
            return curs.fetchall()
    except Exception as e:
        conn.rollback()
        print(e)
    finally:
        conn.close()


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
