import multiprocessing
import time
from typing import List

import requests
from joblib import Parallel, delayed

from .sample import Modality, Sample
from .requester import Requester


class FunctionBuilder:
    def __init__(
        self,
        name: str,
        input_modality: Modality,
        requester: Requester,
        project_id: str = None,
        description: str = "",
        is_public: bool = False,
    ):

        self.requester = requester

        if not project_id:
            resp = self.requester(requests.get, "projects").json()
            if len(resp) < 1:
                project_id = self._post_project()
                print(f"No project found for this account. Project id {project_id} created.")
            elif len(resp) == 1:
                project_id = resp[0]["id"]
            else:
                project_id = resp[0]["id"]
                print(f"Found more than 1 project associated with the credentials. Using {project_id}.")

        self.function_id = self._post_function(name, input_modality, description, is_public, project_id)
        self.local_id_to_server_id = dict()
        self.server_id_to_local_id = dict()
        self.annotated_sample_ids = set()
        self.label_name_to_id = dict()
        print(f"Initialized {self.requester.host}console/functions/{self.function_id}/train")

    def add_label(self, name: str, description: str = ""):
        label_id = self.requester(
            requests.post, f"functions/{self.function_id}/labels", json={"name": name, "description": description}
        ).json()["id"]
        self.label_name_to_id[name] = label_id

    def add_samples(self, samples: List[Sample]):
        cpu_count = multiprocessing.cpu_count()
        sample_ids = Parallel(n_jobs=cpu_count, prefer="threads")(
            delayed(self._post_sample)(sample) for sample in samples
        )
        for sample, server_sample_id in zip(samples, sample_ids):
            self.local_id_to_server_id[sample.id] = server_sample_id
            self.server_id_to_local_id[server_sample_id] = sample.id

    def add_annotations(self, samples: List[Sample]):
        cpu_count = multiprocessing.cpu_count()
        Parallel(n_jobs=cpu_count, prefer="threads")(delayed(self._post_annotation)(sample) for sample in samples)
        self.annotated_sample_ids |= set([sample.id for sample in samples])

    @property
    def nbr_samples(self):
        return len(self.local_id_to_server_id.keys())

    @property
    def nbr_annotations(self):
        return len(self.annotated_sample_ids)

    def has_model(self):
        resp = self.requester(requests.get, f"functions/{self.function_id}/models")
        for model_dict in resp.json():
            if model_dict["trainingPercentage"] == 100:
                return True
        return False

    def sleep_until_has_at_least_one_model(self, poll_interval_sec=1):
        while not self.has_model():
            time.sleep(poll_interval_sec)

    def _post_sample(self, sample):
        if sample.modality.name == "Text":
            inline_data = sample.data
        elif sample.modality.name == "Image":
            inline_data = "data:image/png;base64," + sample.data
        else:
            raise ValueError(f"Unknown modality: {sample.modality}")

        return self.requester(
            requests.post,
            f"functions/{self.function_id}/samples",
            json={
                "externalId": sample.id,
                "input": {"modality": sample.modality.name, "inlineData": inline_data, "referenceUrl": ""},
            },
        ).json()["id"]

    def _post_annotation(self, sample):
        assert sample.id in self.local_id_to_server_id, f"Need to post sample first for id {sample.id}"
        self.requester(
            requests.post,
            f"functions/{self.function_id}/annotations",
            json={
                "sampleId": self.local_id_to_server_id[sample.id],
                "labelId": self.label_name_to_id[sample.label_name],
                "source": "User",
            },
        )

    def _post_function(self, name, input_modality, description, is_public, project_id):
        function_id = self.requester(
            requests.post,
            "functions",
            json={
                "projectId": project_id,
                "name": name,
                "inputModality": input_modality.name,
                "description": description,
                "isPublic": is_public,
            },
        ).json()["id"]
        return function_id

    def _post_project(self):
        project_id = self.requester(requests.post, "projects", json={"name": "Auto-generated", "admins": []}).json()[
            "id"
        ]
        return project_id
