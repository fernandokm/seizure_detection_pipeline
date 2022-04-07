from typing import Iterator, Any, Union

from influxdb_client import InfluxDBClient, WriteOptions
from pyedflib import EdfReader
import rx
import sys

sys.path.append(".")
from src.infrastructure.edf_loader import EdfLoader

def push_influxdb_data(
    data: Any, 
    host: str = "localhost", 
    port:int = 8086, 
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
        time = r.getStartdatetime().timestamp()
        tagslist = ",".join([f"{escape(k)}={escape(v)}" for k, v in tags.items()] + [f"channel={escape(r.getSignalLabels()[channel])}"])
        tagslist = f",{tagslist}" if tagslist else ""
        for val in r.readSignal(channel):
            yield f"{mesurement}{tagslist} {escape(field)}={val} {int(time*1e9)}"
            # yield Point(f"{mesurement}").tag("channel",f"{channel}").field(f"Tension (uV)", val).time(time)
            time += T_sample_real

def push_ecg_to_influxdb(ecg_filepath: str, **kwargs) -> None:
    loader = EdfLoader(ecg_filepath)
    channel_label = loader.get_ecg_candidate_channel()
    channel = loader.channels.index(channel_label)
    data = rx.from_iterable(from_edf(ecg_filepath, channel, mesurement="ecg", tags={"patient": kwargs.get("patient") or ecg_filepath.split("/")[-1].split(".")[0]}, field="Tension (uV)"))
    push_influxdb_data(data, **kwargs)

def escape(s: str) -> str:
    s = str(s)
    return str(s).replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")