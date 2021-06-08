import fire
import os
import csv
import json
import tqdm
import time
import numpy as np
from autonlp import AutoNLP

assert os.getenv("HF_API_KEY"), "HF_API_KEY env variable not set; can't setup connection."

client = AutoNLP()
client.login(token=os.environ["HF_API_KEY"])


def train(dataset_name, n_train):
    project_name = f"{dataset_name}_{n_train}"

    print(f"Setting up project: {project_name}")

    if dataset_name == "ag_news":
        task = "multi_class_classification"
    else:
        task = "binary_classification"

    project = client.create_project(name=project_name, task=task, language="en", max_models=5)
    project.upload(
        filepaths=[f"{dataset_name}_train_{n_train}.csv"],
        split="train",
        col_mapping={"text": "text", "label": "target"},
    )
    project.upload(
        filepaths=[f"{dataset_name}_val_{n_train}.csv"],
        split="valid",
        col_mapping={"text": "text", "label": "target"},
    )
    project.train()


def monitor(project_name):
    project = client.get_project(name=project_name)
    project.refresh()
    models = client.get_metrics(project=project_name)

    print(project)
    print(models)


def evaluate(project_name, model_id, test_file):

    invoke_times = []
    predictions = []
    n_correct = 0
    with open(test_file, "r") as csvfile:
        csvreader = csv.reader(csvfile, delimiter=",", quotechar='"')
        next(csvreader)  # Skip header
        for _, input_text, gt_label_name in tqdm.tqdm(csvreader, total=1000):
            n_words = input_text.split(" ")
            shortened_input = " ".join(n_words[:250])
            t0 = time.time()
            return_ok = False
            while not return_ok:
                prediction = client.predict(project=project_name, model_id=model_id, input_text=shortened_input)
                if (
                    isinstance(prediction, list)
                    and len(prediction) == 1
                    and isinstance(prediction[0], list)
                    and "score" in prediction[0][0]
                ):
                    return_ok = True
                else:
                    print("Call failed, trying again.")
                    time.sleep(2)
            invoke_times.append(time.time() - t0)
            predictions.append(prediction)
            scores = [entry["score"] for entry in prediction[0]]
            ind = np.argmax(scores)
            pred_name = prediction[0][ind]["label"]
            if gt_label_name == pred_name:
                n_correct += 1

    print(f"Project: {project_name}. Accuracy: {n_correct/len(predictions)}")

    with open(f"{project_name}_{model_id}_hf_preds.json", "w") as f:
        json.dump(predictions, f, indent=2)

    with open(f"{project_name}_{model_id}_invoke_times.json", "w") as f:
        json.dump(invoke_times, f, indent=2)


if __name__ == "__main__":
    fire.Fire()
