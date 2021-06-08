import abc
import csv
import os
import random
import fire
from typing import List, Dict

import datasets as huggingface_datasets

from nyckel_utils.sample import Modality, Sample

TRAIN_FRACTION = 0.8
N_TEST = 1000


def hf_split_to_samples(split: huggingface_datasets.splits, label_names: List[str]):
    samples = [
        Sample(
            modality=Modality.Text,
            data=entry["text"],
            label_name=label_names[entry["label"]],
            id=f"{itt}_{split.split}",
        )
        for itt, entry in enumerate(split)
    ]
    return dedupe_samples(samples)


def dedupe_samples(samples: List[Sample]) -> List[Sample]:

    encountered_hashes = set()
    deduped_samples = []
    for sample in samples:
        data_hash = hash(sample.data)
        if data_hash not in encountered_hashes:
            deduped_samples.append(sample)
            encountered_hashes.add(data_hash)

    return deduped_samples


def get_sample_splits(dataset_name, n_train):

    label_names = huggingface_datasets.load_dataset(dataset_name, split="train").features["label"].names
    trainval_samples = hf_split_to_samples(huggingface_datasets.load_dataset(dataset_name, split="train"), label_names)
    random.seed("NyckelML")
    random.shuffle(trainval_samples)

    train_val_cutoff = int(n_train * TRAIN_FRACTION)
    train_samples = trainval_samples[:train_val_cutoff]
    val_samples = trainval_samples[train_val_cutoff:n_train]

    test_samples = hf_split_to_samples(huggingface_datasets.load_dataset(dataset_name, split="test"), label_names)
    random.shuffle(test_samples)
    test_samples = test_samples[:N_TEST]

    return train_samples, val_samples, test_samples


def write_data(samples_dict: Dict, filename):
    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter=",", quotechar='"')
        writer.writerow(["split", "text", "label"])
        for split_name, split_samples in samples_dict.items():
            for sample in split_samples:
                writer.writerow([split_name, sample.data, sample.label_name])


def build_data_files(dataset_name="imdb", n_train=500):

    assert dataset_name in ["imdb", "ag_news"]
    print(f"Prepare {dataset_name} with {n_train} train samples.")
    train_samples, val_samples, test_samples = get_sample_splits(dataset_name, n_train)

    write_data({"training": train_samples}, f"{dataset_name}_train_{n_train}.csv")
    write_data({"validation": val_samples}, f"{dataset_name}_val_{n_train}.csv")
    write_data({"test": test_samples}, f"{dataset_name}_test.csv")
    write_data({"training": train_samples, "validation": val_samples}, f"{dataset_name}_trainval_{n_train}.csv")
    write_data(
        {"training": train_samples, "validation": val_samples, "test": test_samples},
        f"{dataset_name}_all_{n_train}.csv",
    )


if __name__ == "__main__":
    fire.Fire(build_data_files)
