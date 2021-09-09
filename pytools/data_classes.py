import os
from dataclasses import dataclass
from typing import List, Optional

assert os.getenv("NYCKEL_CLIENT_ID"), "NYCKEL_CLIENT_ID env variable not set; can't setup connection."
assert os.getenv("NYCKEL_CLIENT_SECRET"), "NYCKEL_CLIENT_SECRET env variable not set; can't setup connection."


@dataclass
class Sample:
    annotation_label_name: Optional[str]
    prediction_label_name: Optional[str]
    prediction_label_confidence: Optional[float]
    sample_file: str


@dataclass
class Function:
    name: str
    modality: str
    samples: List[Sample]
