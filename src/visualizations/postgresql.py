import psycopg2
import csv

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
    cursor.execute(f"DROP TABLE IF EXISTS {table}")
    file = content if type(content) == dict else next(content)  # if generator, get file
    first_row: dict = next(file)
    columns_sql = ", ".join(
        (f"{column} {get_data_type(value)}" for column, value in first_row.items())
    )
    cursor.execute(f"CREATE TABLE {table} ({columns_sql})")
    fill_table(cursor, table, file, first_row=first_row)


def get_data_type(data):
    """
    Returns data type of data
    """
    association = [
        (int, "integer"),
        (float, "float"),
        (bool, "boolean"),
        (str, "varchar(255)"),
    ]
    for dt_type, dt_name in association:
        if _check_type(data, dt_type):
            return dt_name


def _check_type(data, dt_type):
    """
    Check if data is of type
    """
    if dt_type == bool:
        try:
            return str(data).lower() in ["true", "false"]
        except:
            return False
    try:
        dt_type(data)
        return True
    except:
        return False


def fill_table(cursor, table, content, first_row=None):
    """
    Fills existing table in postgresql with content
    cursor: cursor
    table: table name
    content: table content
    """
    if first_row:
        columns = ", ".join(first_row.keys())
        values = ", ".join(map(lambda column: f"%({column})s", first_row.keys()))
        cursor.execute(f"INSERT INTO {table} ({columns}) VALUES ({values})", first_row)
    for row in content:
        columns = ", ".join(row.keys())
        values = ", ".join(map(lambda column: f"%({column})s", row.keys()))
        cursor.execute(f"INSERT INTO {table} ({columns}) VALUES ({values})", row)


def get_data_from_csv(filepath):
    """
    Transforms data from csv to list of dicts for each line
    """
    with open(filepath, "r") as csv_file:
        yield csv.DictReader(csv_file)


def get_data_from_csv_dict(csv_files):
    """
    Transforms data from dict of csv files (table name: csv filepath) to push_postgresql data format
    """
    data = {}
    for table, filepath in csv_files.items():
        data[table] = get_data_from_csv(filepath)
    return data
