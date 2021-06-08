from enum import Enum
from typing import List, Optional
from dataclasses import dataclass


class Modality(Enum):
    Text = 1
    Image = 2


@dataclass
class Sample:

    modality: Modality
    id: str  # Unique string token for this sample.
    data: str  # The actual data.
    label_name: str  # Label name.
