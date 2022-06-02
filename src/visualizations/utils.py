from typing import Tuple
from .log import log

import re

def split_patient_string(patient_string: str) -> Tuple[str]:
    """
    Splits a patient string (such as '00004671_s007_t000') into a tuple patient, session ('00004671','s007_t000')
    """
    m = re.match(r"^([^_]+)_(.+)$", patient_string)
    if not m:
        raise Exception("No match in patient_string :" + str(patient_string))
    log(m.group(1))
    log(m.group(2))
    return m.group(1,2)
