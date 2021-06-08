import csv
import json

import fire
import numpy as np


def accuracy(test_file, pred_file):

    with open(test_file, "r") as csvfile:
        csvreader = csv.reader(csvfile, delimiter=",", quotechar='"')
        next(csvreader)
        gts = [row[2] for row in csvreader]

    with open(pred_file, "r") as f:
        preds = json.load(f)

    n_correct = 0
    for pred, gt in zip(preds, gts):
        scores = [entry["score"] for entry in pred[0]]
        ind = np.argmax(scores)
        pred_name = pred[0][ind]["label"]
        if pred_name == gt:
            n_correct += 1
    print(n_correct / 1000)


if __name__ == "__main__":
    fire.Fire(accuracy)
