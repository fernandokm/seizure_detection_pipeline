import random
from influxdb_client import InfluxDBClient
import os
import json
from .postgresql import query as postgresql_query

# from .log import log
from itertools import islice

IDB_HOST = "localhost"
IDB_PORT = os.environ.get("INFLUXDB_PORT")
IDB_USERNAME = os.environ.get("INFLUXDB_USERNAME")
IDB_PASSWORD = os.environ.get("INFLUXDB_PASSWORD")
IDB_DATABASE = os.environ.get("INFLUXDB_DATABASE")

PATIENT_DASHBOARD = os.path.join(
    os.path.dirname(__file__), "../../conf/provisioning/dashboards/patient.json"
)
HOME_DASHBOARD = os.path.join(
    os.path.dirname(__file__), "../../conf/provisioning/dashboards/main.json"
)
PATIENT_NAMES_LINES = 18239
PATIENT_NAMES_FILE = os.path.join(os.path.dirname(__file__), "names.txt")


def generate_home_dashboard(
    filepath: str,
    host: str,
    port: str,
    database: str,
    retention_policy: str,
    username: str,
    password: str,
):
    """
    Generate home dashboard
    """
    home_dashboard = read_dashboard(filepath)
    patient_dashboard = read_dashboard(PATIENT_DASHBOARD)
    start_times, end_times, patient_ids = get_influxdb_data(
        host=host,
        port=port,
        database=database,
        retention_policy=retention_policy,
        username=username,
        password=password,
    )
    # Generate links pannel
    links = generate_patient_links(
        start_times,
        end_times,
        patient_ids,
        patient_dashboard_uid=patient_dashboard["uid"],
    )
    home_dashboard["panels"][0]["html_data"] = generate_links_pannel(links)
    write_dashboard(home_dashboard, filepath)


def generate_links_pannel(links: list) -> str:
    return f"""
    <div class="panel-container">
        <div class="panel-content">
            <div class="panel-content-text">
                <div class="panel-content-text-row">

                <ul>
                    {"".join('<li>{link}</li>'.format(link=link) for link in links)}
                </ul>
                </div>
            </div>
        </div>
    </div>
    """


def generate_patient_links(
    start_times, end_times, patient_ids, patient_dashboard_uid=0
):
    """
    Generate session links
    """
    links = []
    for start_time, end_time, patient_id in zip(start_times, end_times, patient_ids):
        patient_label = generate_patient_label(patient_id)
        links.append(
            f"<a href='/d/{patient_dashboard_uid}/patient?orgId=1&var-patient={patient_id}&from={start_time}&to={end_time}'>{patient_label}{generate_patient_subtitle(patient_id)}</a>"
        )
    return links


def generate_patient_subtitle(patient_id) -> list:
    real_crises = postgresql_query(
        host=os.environ.get("POSTGRES_HOST_URL"),
        database=os.environ.get("POSTGRES_DATABASE"),
        username=os.environ.get("POSTGRES_USER"),
        password=os.environ.get("POSTGRES_PASSWORD"),
        query=f"SELECT * FROM crises WHERE patient_id = {patient_id} AND type == 'real'",
    )
    predicted_crises = postgresql_query(
        host=os.environ.get("POSTGRES_HOST_URL"),
        database=os.environ.get("POSTGRES_DATABASE"),
        username=os.environ.get("POSTGRES_USER"),
        password=os.environ.get("POSTGRES_PASSWORD"),
        query=f"SELECT * FROM crises WHERE patient_id = {patient_id} AND type == 'predicted'",
    )

    return f"<div class='session-subtitle'> {len(real_crises)} vraies Crises, {len(predicted_crises)}</div>"


def generate_patient_label(patient_id: int) -> str:
    """
    Generates a patient label with form "Name (id)"
    """
    l = random.randint(0, PATIENT_NAMES_LINES - 1)
    with open(PATIENT_NAMES_FILE) as f:
        skipped = islice(f, l, l + 1)
        name = next(skipped).strip()
    return f"{name} ({patient_id})"


def get_influxdb_data(
    host: str = "localhost",
    port: int = 8086,
    database: str = "default",
    retention_policy: str = "autogen",
    username: str = "root",
    password: str = "root",
    **kwargs,
) -> None:
    url = f"http://{host}:{port}"
    token = f"{username}:{password}"
    bucket = f"{database}/{retention_policy}"
    with InfluxDBClient(url, token, org="-") as client:
        patients_ids = get_patients_ids(client, bucket)
        start_times, end_times = [], []
        for patient_id in patients_ids:
            s, e = get_window(client, bucket, patient_id)
            start_times.append(s)
            end_times.append(e)
    return start_times, end_times, patients_ids


def get_window(client, bucket, patient_id):
    query = f"""
    from(bucket: "{bucket}")
    |> range(start: -20y, stop: now())
    |> filter(fn: (r) => 
        r._measurement == "ecg" and 
        r.patient == "{patient_id}")
    |> first(column: "_time")
    |> keep(columns: ["_time"])  
    |> map(fn: (r) => ({{
        "_time": uint(v: r._time),
    }}))
    """
    query_api = client.query_api()
    r = query_api.query_stream(org="-", query=query)
    s = next(r).values.get("_time", None)
    query = f"""
    from(bucket: "{bucket}")
    |> range(start: -20y, stop: now())
    |> filter(fn: (r) => 
        r._measurement == "ecg" and 
        r.patient == "{patient_id}")
    |> last(column: "_time")
    |> keep(columns: ["_time"])  
    |> map(fn: (r) => ({{
        "_time": uint(v: r._time),
    }}))
    """
    r = query_api.query_stream(org="-", query=query)
    e = next(r).values.get("_time", None)
    return s // int(1e6), e // int(1e6)


def get_patients_ids(client: InfluxDBClient, bucket: str) -> list:
    query = f"""import "influxdata/influxdb/v1"
    v1.tagValues(bucket: "{bucket}", tag: "patient", predicate: (r) => true, start: -20y)"""
    query_api = client.query_api()
    r = query_api.query_stream(org="-", query=query)
    patients_ids = [rec.values.get("_value", None) for rec in r]
    return patients_ids


def read_dashboard(path: str) -> str:
    with open(path, "r") as f:
        return json.load(f)


def write_dashboard(dashboard: str, path: str):
    with open(path, "w") as f:
        json.dump(dashboard, f, indent=4)


def main():
    generate_home_dashboard(
        filepath=HOME_DASHBOARD,
        host=IDB_HOST,
        port=IDB_PORT,
        database=IDB_DATABASE,
        retention_policy="autogen",
        username=IDB_USERNAME,
        password=IDB_PASSWORD,
    )


if __name__ == "__main__":
    main()
