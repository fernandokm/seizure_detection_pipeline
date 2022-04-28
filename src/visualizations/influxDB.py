from src.infrastructure.edf_loader import EdfLoader
from src.visualizations.log import log
from typing import Iterator, Any, Union

import csv
from influxdb_client import InfluxDBClient, WriteOptions
from pyedflib import EdfReader
import rx
import datetime
from numpy import float64


def push_influxdb_data(
    data: Any,
    host: str = "localhost",
    port: int = 8086,
    database: str = "default",
    retention_policy: str = "autogen",
    username: str = "root",
    password: str = "root",
    **kwargs
) -> None:
    """
    Push data to influxdb
    data: client write api record field, can be str, Point, dict, bytes, Observable, NamedTuple, or an iterable of one of these types
    """
    url = f"http://{host}:{port}"
    token = f"{username}:{password}"
    bucket = f"{database}/{retention_policy}"
    with InfluxDBClient(url, token, org="-") as client:
        with client.write_api(write_options=WriteOptions(batch_size=50000, flush_interval=10000)) as write_api:
            write_api.write(bucket, record=data)


def from_edf(filepath: str, channel: int, mesurement: Union[str, None] = None, tags: dict = {}, field: str = "Field") -> Iterator[str]:
    """
    Get points from edf file
    filepath: filepath
    channel: channel
    """
    mesurement = escape(mesurement or filepath)
    with EdfReader(filepath) as r:
        T_sample_real = 1/r.getSampleFrequency(channel)
        time = r.getStartdatetime()
        tagslist = ",".join([f"{escape(k)}={escape(v)}" for k, v in tags.items(
        )] + [f"channel={escape(r.getSignalLabels()[channel])}"])
        tagslist = f",{tagslist}" if tagslist else ""
        for val in r.readSignal(channel):
            yield f"{mesurement}{tagslist} {escape(field)}={escapevalue(val)} {to_nanoseconds(time)}"
            # yield Point(f"{mesurement}").tag("channel",f"{channel}").field(f"Tension (uV)", val).time(time)
            time += datetime.timedelta(seconds=T_sample_real)


def push_ecg_to_influxdb(ecg_filepath: str, **kwargs) -> None:
    loader = EdfLoader(ecg_filepath)
    channel_label = loader.get_ecg_candidate_channel()
    channel = loader.channels.index(channel_label)
    data = rx.from_iterable(from_edf(ecg_filepath, channel, mesurement="ecg", tags={"patient": kwargs.get(
        "patient") or ecg_filepath.split("/")[-1].split(".")[0]}, field="Tension (uV)"))
    push_influxdb_data(data, **kwargs)


def escape(s: str) -> str:
    s = str(s)
    return str(s).replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")


def escapevalue(value: Any) -> str:
    """
    Escape value if it can't be interpreted as a finite number
    """
    try:
        # drop unreadable values
        if abs(float(value)) in [float("inf"), float("nan")]:
            return ""
        return str(value)
    except:
        if len(str(value)) > 0:
            return f"\"{value}\""
        else:
            return ""


def push_csv_features_to_influxdb(csv_filepath: str, **kwargs) -> None:
    data = rx.from_iterable(from_csv(csv_filepath, measurement="features", tags={"patient": kwargs.get(
        "patient") or csv_filepath.split("/")[-1].split(".")[0]}, time_column="timestamp"))
    push_influxdb_data(data, **kwargs)


def from_csv(csv_filepath: str, measurement: Union[None, str] = None, tags: dict = {}, time_column: str = "timestamp", **kwargs) -> Iterator[str]:
    """
    Get points from csv file
    csv_filepath: filepath
    """
    with open(csv_filepath, "r") as f:
        reader = csv.DictReader(f)
        measurement = escape(measurement or csv_filepath)
        tagslist = ",".join(
            [f"{escape(k)}={escape(v)}" for k, v in tags.items()])
        tagslist = f",{tagslist}" if tagslist else ""
        for row in reader:
            time = row[time_column]
            for k, v in row.items():
                value = escapevalue(v)
                if k == time_column or value == "":
                    continue
                yield f"{measurement}{tagslist} {escape(k)}={value} {to_nanoseconds(time)}"


def to_nanoseconds(date_time: Any, mult_to_seconds=1):
    """
    TODO: comment better
    Convert date_time to nanoseconds
    date_time: can be str (int seconds timestamp), str (DD-MM-YYYY HH:MM:SS.m), datetime, int or float (in seconds)
    """
    mult = 1e9*mult_to_seconds
    if type(date_time) == str:
        try:
            return int(float(date_time)*mult)
        except:
            return int(datetime.datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S.%f").timestamp()*1e9)
    elif type(date_time) in [int, float, float64]:
        return int(date_time*mult)
    elif type(date_time) == datetime.datetime:
        return int(date_time.timestamp()*1e9)
    raise TypeError("Invalid date_time type: {}".format(type(date_time)))

# TODO : add function to test if patient data already exists
