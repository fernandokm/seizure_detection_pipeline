import os
from datetime import datetime
import influxDB
import postgresql

POSTGRES_HOST_URL = os.environ.get("POSTGRES_LOCALHOST")
POSTGRES_DATABASE = os.environ.get("POSTGRES_DATABASE")
POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")

IDB_HOST = "localhost"
IDB_PORT = os.environ.get("INFLUXDB_PORT")
IDB_USERNAME = os.environ.get("INFLUXDB_USERNAME")
IDB_PASSWORD = os.environ.get("INFLUXDB_PASSWORD")
IDB_DATABASE = os.environ.get("INFLUXDB_DATABASE")

EDF_SOURCES = {
    3281: "data/tuh/dev/01_tcp_ar/002/00003281/00003281_s001_t001.edf"
}

CSV_SOURCES = {
    3281: "output/cons_00003281_s001_t001_t001.csv"
}


def generate_postgresql_data(csv_files: dict = {}):
    """
    Generate data in postgresql from csv files
    """
    data = postgresql.get_data_from_csv_dict(csv_files)
    postgresql.push_postgresql_data(
        data=data,
        host=POSTGRES_HOST_URL,
        database=POSTGRES_DATABASE,
        username=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )


def generate_influxdb_data(edf_files: dict = {}, csv_files: dict = {}):
    """ 
    Generate data in influxdb from edf files
    edf_files: input edf files {}
    """
    for patient, file in edf_files.items():
        influxDB.push_ecg_to_influxdb(file, patient=patient, host=IDB_HOST, port=IDB_PORT,
                                      username=IDB_USERNAME, password=IDB_PASSWORD, database=IDB_DATABASE)
    for patient, file in csv_files.items():
        influxDB.push_csv_features_to_influxdb(
            file, patient=patient, host=IDB_HOST, port=IDB_PORT, username=IDB_USERNAME, password=IDB_PASSWORD, database=IDB_DATABASE)


def log(msg):
    """
    Log message
    """
    print(f"{datetime.now().strftime('%H:%M:%S')}: {msg}")


if __name__ == "__main__":
    log("Starting execution")
    # generate_postgresql_data(CSV_SOURCES)
    generate_influxdb_data(EDF_SOURCES, CSV_SOURCES)
    log("Execution finished")
