import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Sample:
    annotation_label_name: Optional[str]
    prediction_label_name: Optional[str]
    prediction_label_confidence: Optional[float]
    sample_file: str


@dataclass
class Function:
    name: Optional[str]
    modality: str
    samples: List[Sample]
    label_names: List[str]
