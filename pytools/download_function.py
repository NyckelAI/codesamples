import json
import os
from dataclasses import asdict
from typing import List

import fire

from data_classes import Function, Sample
from requester import repeated_get, requester_factory
from utils import load_image


def download_function(function_id: str):

    print(f"Downloading function {function_id} from www.nyckel.com... ")

    requester = requester_factory()
    function_dict = repeated_get(requester, f"/functions/{function_id}")
    sample_dict_list = repeated_get(requester, f"/functions/{function_id}/samples")
    label_dict_list = repeated_get(requester, f"/functions/{function_id}/labels")
    os.makedirs(f"{function_id}/data", exist_ok=True)

    if function_dict["inputModality"] == "Image":
        print(
            "Warning: Images may get compressed when uploaded to Nyckel. Downloaded images may therefore be smaller than the originals."
        )

    samples: List[Sample] = []
    for sample_dict in sample_dict_list:
        if "bestAnnotation" in sample_dict and sample_dict["bestAnnotation"] is not None:
            annotation_label_name = next(
                filter(lambda label: label["id"] == sample_dict["bestAnnotation"]["labelId"], label_dict_list)
            )["name"]
        else:
            annotation_label_name = None

        if "bestPrediction" in sample_dict and sample_dict["bestPrediction"] is not None:
            prediction_label_name = next(
                filter(lambda label: label["id"] == sample_dict["bestPrediction"]["labelId"], label_dict_list)
            )["name"]
            prediction_label_confidence = sample_dict["bestPrediction"]["confidence"]
        else:
            prediction_label_confidence = None
            prediction_label_name = None

        if sample_dict["input"]["modality"] == "Image":
            img = load_image(sample_dict["input"]["inlineData"])
            sample_file = f"{function_id}/data/{sample_dict['id']}.jpg"
            img.save(sample_file)
        else:
            text = sample_dict["input"]["inlineData"]
            sample_file = f"{function_id}/data/{sample_dict['id']}.txt"
            with open(sample_file, "w") as f:
                f.write(text)

        samples.append(
            Sample(
                annotation_label_name=annotation_label_name,
                prediction_label_name=prediction_label_name,
                prediction_label_confidence=prediction_label_confidence,
                sample_file=sample_file,
            )
        )

    function = Function(
        name=function_dict["name"],
        modality=function_dict["inputModality"],
        samples=samples,
        label_names=[entry["name"] for entry in label_dict_list],
    )

    with open(f"{function_id}/function.json", "w") as f:
        json.dump(asdict(function), f, indent=2)

    print(f"Function {function_id} downloaded to {os.path.dirname(os.path.abspath(__file__))}/{function_id}")


if __name__ == "__main__":
    fire.Fire(download_function)
