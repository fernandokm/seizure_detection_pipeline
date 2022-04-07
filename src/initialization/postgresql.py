import psycopg2
import csv

def push_postgresql_data(
    data: dict,
    host: str,
    database: str,
    username: str,
    password: str,
    port: int = 5432
):
    """
    Push data to postgresql
    data: input data {
        table_name: [{column1: value1, column2: value2}, {column1: value1, column2: value2},...]
    }
    """
    conn = psycopg2.connect(host=host, database=database, user=username, password=password, port=port)
    try:
        with conn.cursor() as curs:
            for table,content in data.items():
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
    columns_sql = ", ".join((map(lambda column: f"{column} varchar(255)" if type(column) == str else f"{column} integer", first_row.keys())))
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
        values_sql = ", ".join((map(lambda column: f"'{row[column]}'" if type(row[column]=="str") else f"{row[column]}", row.keys())))
        cursor.execute(f"INSERT INTO {table} ({columns_sql}) VALUES ({values_sql})")

def get_data_from_csv(filepath):
    """
    Not used
    """
    with open(filepath, "r") as csv_file:
        reader = csv.DictReader(csv_file)
        return list(reader)

def get_data_from_csv_dict(csv_files):
    """
    Not used
    """
    data = {}
    for table, filepath in csv_files.items():
        data[table] = get_data_from_csv(filepath)
    return data
