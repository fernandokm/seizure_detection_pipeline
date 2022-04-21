from datetime import datetime
import lime
from lime import lime_tabular
from typing import Dict, List, Union


def lime_barchart_to_postgresql_data(
    exp: lime.explanation.Explanation,
    timestamp: str,
    patient_id: int,
    session_id: int,
    table_name: str = "lime_barchart",
) -> Dict[str, List[Dict[str, Union[datetime.timestamp, int, float, str]]]]:
    """
    Converts a lime barchart to a dictionnary uploadable as postgresql data

    Parameters
    ----------
    exp: lime.explanation.Explanation
        the lime explainer used to plot the barchart graph
    timestamp: str
        timestamp of the prediction, with the following format : "YYYY-MM-DD HH:MM:SS.sss"
    patient_id: int
        id of the patient who's crisis are predicted
    session_id: int
        id of the session during which the prediction was made
    table_name: str = "lime_barchart"
        name of the postgresql table in which the data is stored

    Returns
    -------
    Dict[str, List[Dict[str, Union[datetime.timestamp, int, float, str]]]]
        a dictionnary respecting the postgresql data format
    """
    data = {table_name: []}
    for (feature_name, lime_coefficient) in exp.as_list():
        data[table_name].append(
            {
                "timestamp": datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f"),
                "patient_id": patient_id,
                "session_id": session_id,
                "feature_name": feature_name,
                "lime_coefficient": lime_coefficient,
            }
        )
    return data


def merge_postgresql_data(data_to_merge_on, data_to_merge):
    """
    Merges two dictionnary respecting the postgresql data format into one.
    If a table in data_to_merge is not in data_to_merge_on, then it is added to it
    Else, if the table already exists, they are concatenated.
    data_to_merge_on will be modified in place and returned as the result

    Parameters
    ----------
    data_to_merge_on : Dict[str, List[Dict[str, Union[datetime.timestamp, int, float, str]]]]
        a dictionnary respecting the postgresql data format
    data_to_merge : Dict[str, List[Dict[str, Union[datetime.timestamp, int, float, str]]]]
        an other dictionnary respecting the postgresql data format

    Returns
    -------
    Dict[str, List[Dict[str, Union[datetime.timestamp, int, float, str]]]]
        a dictionnary resulting of the merging of the two arguments
    """
    for table_name in data_to_merge_on:
        if table_name in data_to_merge:
            data_to_merge_on[table_name].append(data_to_merge[table_name])
        else:
            data_to_merge_on[table_name] = data_to_merge[table_name]
    return data_to_merge_on


# pd.DataFrame : 1 column par feature, 1 column shap value par feature, timestamp (str)

if __name__ == "__main__":

    from src.initialization.postgresql import push_postgresql_data

    exemple_exp_as_list = [
        ("sdnn > 45.06", 0.02411322827453069),
        ("37.81 < sdsd <= 47.72", -0.010875025043483475),
        ("1.00 < nni_50 <= 3.00", -0.010813409903775757),
        ("120.00 < range_nni <= 156.00", -0.008063098295348344),
        ("Modified_csi > 752.78", -0.00746024078046046),
        ("0.05 < cvnni <= 0.06", -0.006936012779760039),
    ]

    class FalseExp:
        def __init__(self, list):
            self.list = list

        def as_list(self):
            return self.list

    exp = FalseExp(exemple_exp_as_list)
    timestamp = "2006-10-09 09:04:50.492"
    patient_id = 1234
    session_id = 5678

    data = lime_barchart_to_postgresql_data(exp, timestamp, patient_id, session_id)

    print(data)

    push_postgresql_data(data, "localhost", "grafana", "postgres", "wdkjsdk8hcjbw")
