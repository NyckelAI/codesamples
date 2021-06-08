import csv
import json
import os
import time

import fire
import requests
from tqdm import tqdm

from nyckel_utils.function import FunctionBuilder
from nyckel_utils.requester import requester_factory
from nyckel_utils.sample import Modality, Sample

assert os.getenv("NYCKEL_CLIENT_ID"), "NYCKEL_CLIENT_ID env variable not set; can't setup connection."
assert os.getenv("NYCKEL_CLIENT_SECRET"), "NYCKEL_CLIENT_SECRET env variable not set; can't setup connection."

requester = requester_factory()


def csv_to_samples(file_path):
    with open(file_path, "r") as csvfile:
        csvreader = csv.reader(csvfile, delimiter=",", quotechar='"')
        next(csvreader)
        samples = []
        for cnt, row in enumerate(csvreader):
            samples.append(
                Sample(
                    modality=Modality.Text,
                    id=f"{os.path.basename(file_path)}-{cnt}",
                    label_name=row[2],
                    data=row[1],
                )
            )
    return samples


def train(dataset_name, n_train, with_val=True):

    function_name = f"{dataset_name}_{n_train}"
    train_samples = csv_to_samples(f"{dataset_name}_train_{n_train}.csv")

    builder = FunctionBuilder(name=function_name, input_modality=Modality.Text, requester=requester)
    for label_name in list(set([sample.label_name for sample in train_samples])):
        builder.add_label(label_name)

    t0 = time.time()
    print("Uploading train data...")
    builder.add_samples(train_samples)
    builder.add_annotations(train_samples)
    if with_val:
        print("Uploading validation data...")
        val_samples = csv_to_samples(f"{dataset_name}_val_{n_train}.csv")
        builder.add_samples(val_samples)
        builder.add_annotations(val_samples)
    else:
        print("Skipping val data.")
    print("Training...")
    builder.sleep_until_has_at_least_one_model()

    print(f"Training of function {builder.function_id} complete in {time.time()-t0:.1f} seconds.")


def evaluate(function_id, test_file):

    test_samples = csv_to_samples(test_file)

    t0 = time.time()
    invoke_times = []
    predictions = []
    n_correct = 0
    for sample in tqdm(test_samples):
        t0 = time.time()
        resp = requester(
            requests.post,
            f"functions/{function_id}/invoke",
            json={"data": f"[{sample.data}]"},
        )
        invoke_times.append(time.time() - t0)
        prediction = resp.json()
        predictions.append(prediction)
        if prediction["name"] == sample.label_name:
            n_correct += 1

    print(f"Project: {test_file} {function_id}. Accuracy: {n_correct/len(predictions):.2f}")

    with open(f"{test_file}_{function_id}_nyckel_preds.json", "w") as f:
        json.dump(predictions, f, indent=2)

    with open(f"{test_file}_{function_id}_nyckel_invoke_times.json", "w") as f:
        json.dump(invoke_times, f, indent=2)


if __name__ == "__main__":
    fire.Fire()
