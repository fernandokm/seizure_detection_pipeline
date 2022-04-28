from influxdb_client import InfluxDBClient
import os
import json
from .log import log

IDB_HOST = "localhost"
IDB_PORT = os.environ.get("INFLUXDB_PORT")
IDB_USERNAME = os.environ.get("INFLUXDB_USERNAME")
IDB_PASSWORD = os.environ.get("INFLUXDB_PASSWORD")
IDB_DATABASE = os.environ.get("INFLUXDB_DATABASE")

PATIENT_DASHBOARD = "./conf/provisioning/dashboards/patient.json"
HOME_DASHBOARD = "./conf/provisioning/dashboards/main.json"


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


def generate_confusion_matrix():
    """
        #main {
    width: 100%;
    height: 100%;
    }

    .line {
    display: flex;
    justify-content: center;
    width:100%;
    height: 50%;
    }
    .line > div {
    width: 50%;
    text-align: center;
    color: white;
    display: flex;
    justify-content:center;
    align-items: center;
    font-size: 1.7rem;
    }
    #square1 {
    background: red;
    }
    #square2 {
    background: blue;
    }
    #square3 {
    background: yellow;
    color: black
    }

    #square4 {
    background: green;
    }
    """
    """
    <div id='main'>
<div class='line'>
<div id='square1'>
96
</div>
<div id='square2'>
1067
</div>
</div>
<div class='line'>
<div id='square3'>
158 896
</div>
<div id='square4'>
14 346
</div>
</div>
</div>

    """
    pass


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
        patient_label = f"Patient {patient_id}"
        links.append(
            f"<a href='/d/{patient_dashboard_uid}/patient?orgId=1&var-patient={patient_id}&from={start_time}&to={end_time}'>{patient_label}{generate_patient_subtitle()}</a>"
        )
    return links


def generate_patient_subtitle() -> list:
    return (
        "<div class='session-subtitle'>x vraies Crises, prédictions justes à x%</div>"
    )


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
    patients_ids = [int(rec.values.get("_value", None)) for rec in r]
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
