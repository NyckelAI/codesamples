import csv
import json
import os
import time

import fire
import numpy as np
import requests
from tqdm import tqdm

assert os.getenv("GCP_BEARER_TOKEN"), "GCP_BEARER_TOKEN env variable not set; can't setup connection."
assert os.getenv("GCP_INVOKE_ENDPOINT"), "GCP_INVOKE_ENDPOINT env variable not set; can't setup connection."

gcp_bearer_token = os.environ["GCP_BEARER_TOKEN"]
gcp_invoke_endpoint = os.environ["GCP_INVOKE_ENDPOINT"]


def evaluate(test_file):

    predictions = []
    invoke_times = []
    n_correct = 0
    with open(test_file, "r") as csvfile:
        csvreader = csv.reader(csvfile, delimiter=",", quotechar='"')
        next(csvreader)
        for _, text, gt_label_name in tqdm(csvreader, total=1000):
            t0 = time.time()
            data = {"instances": [{"mimeType": "text/plain", "content": text}]}
            resp = requests.post(
                gcp_invoke_endpoint,
                json=data,
                headers={"authorization": "Bearer " + gcp_bearer_token},
            )
            prediction = resp.json()

            invoke_times.append(time.time() - t0)
            predictions.append(prediction)

            scores = prediction["predictions"][0]["confidences"]
            pred_names = prediction["predictions"][0]["displayNames"]
            ind = np.argmax(scores)
            pred_label_name = pred_names[ind]
            if pred_label_name == gt_label_name:
                n_correct += 1

    print(f"Project: {test_file}. Accuracy: {n_correct/len(predictions)}")

    with open(f"{test_file}_google_preds.json", "w") as f:
        json.dump(predictions, f, indent=2)

    with open(f"{test_file}_google_invoke_times.json", "w") as f:
        json.dump(invoke_times, f, indent=2)


if __name__ == "__main__":
    fire.Fire()
