import base64
import json
import multiprocessing
from typing import List

import fire
import requests
from dacite import from_dict
from joblib import Parallel, delayed

from data_classes import Function, Sample
from requester import Requester, requester_factory


class FunctionBuilder:
    def __init__(
        self,
        name: str,
        input_modality: str,
        requester: Requester,
        project_id: str = None,
        description: str = "",
        is_public: bool = False,
    ):

        self.requester = requester
        self.input_modality = input_modality

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
        self.label_name_to_id = dict()
        print(f"Initialized {self.requester.host}console/functions/{self.function_id}/train")

    def add_label(self, name: str, description: str = ""):
        label_id = self.requester(
            requests.post, f"functions/{self.function_id}/labels", json={"name": name, "description": description}
        ).json()["id"]
        self.label_name_to_id[name] = label_id

    def add_samples(self, samples: List[Sample]):
        cpu_count = multiprocessing.cpu_count()
        Parallel(n_jobs=cpu_count, prefer="threads")(delayed(self._post_sample)(sample) for sample in samples)

    def _post_sample(self, sample: Sample):
        if self.input_modality == "Text":
            with open(sample.sample_file) as f:
                inline_data = f.read()
        elif self.input_modality == "Image":
            # img = Image.open(os.path.join(function_folder, sample.sample_file))
            # buffered = BytesIO()
            # img.save(buffered, format="JPEG")
            with open(sample.sample_file, "rb") as f:
                encoded_string = base64.b64encode(f.read()).decode("utf-8")
            inline_data = "data:image/png;base64," + encoded_string
        else:
            raise ValueError(f"Unknown modality: {sample.modality}")

        new_sample_id = self.requester(
            requests.post,
            f"functions/{self.function_id}/samples",
            json={
                "externalId": sample.sample_file,
                "input": {"modality": self.input_modality, "inlineData": inline_data, "referenceUrl": ""},
            },
        ).json()["id"]

        if sample.annotation_label_name:
            self.requester(
                requests.post,
                f"functions/{self.function_id}/annotations",
                json={
                    "sampleId": new_sample_id,
                    "labelId": self.label_name_to_id[sample.annotation_label_name],
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
                "inputModality": input_modality,
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


def upload_function(function_id: str):

    with open(f"{function_id}/function.json") as f:
        function = from_dict(data_class=Function, data=json.load(f))

    builder = FunctionBuilder(function.name, input_modality=function.modality, requester=requester_factory())

    for label_name in function.label_names:
        builder.add_label(label_name)

    builder.add_samples(function.samples)


if __name__ == "__main__":
    fire.Fire(upload_function)
