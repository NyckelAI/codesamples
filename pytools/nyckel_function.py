import base64
import os
import time
from abc import abstractmethod
from glob import glob
from io import BytesIO
from typing import Dict, List, Tuple, Union

from joblib import Parallel, delayed
from PIL import Image
from tqdm import tqdm

from requester import Requester

requester_v09 = Requester(api_version="v0.9")
requester_v1 = Requester(api_version="v1")
supported_modalities = ["Image", "Text", "Tabular"]

InputData = Union[str, Image.Image]
LabelId = str
LabelName = str
Sample = Tuple[InputData, LabelName]


def base64encoded_image(img: Image):
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    encoded_string = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return "data:image/jpg;base64," + encoded_string


class NyckelFunction:
    def __init__(
        self,
        name: str,
        modality: str,
        description: str,
        function_id: str,
        project_id: str,
        label_name_to_id: Dict[str, str],
        has_model: bool,
    ):

        self.name = name
        self.modality = modality
        self.description = description
        self.function_id = function_id
        self.project_id = project_id
        self.label_name_to_id = label_name_to_id
        self.has_model = has_model

    @classmethod
    def new(cls, name: str, modality: str, description: str = "", is_public=False):
        assert modality in supported_modalities
        project_id = cls._get_project_id()
        function_id = cls._post_function(project_id, name, modality, description, is_public)
        print(f"Initialized {requester_v1.host}console/functions/{function_id}/train")
        return cls(name, modality, description, function_id, project_id, {}, False)

    def __call__(self, input_data: InputData):
        if not self.has_model:
            while not self.has_model:
                try:
                    self._timed_invoke(input_data)
                    self.has_model = True
                except RuntimeError as e:
                    if "No model available to invoke function" in str(e):
                        print("Waiting for model training to finish ...")
                        time.sleep(1)
        else:
            self._timed_invoke(input_data)

    def _timed_invoke(self, input_data: InputData):
        t0 = time.time()
        resp = requester_v1.post(
            f"functions/{self.function_id}/invoke", body={"data": self._input_data_to_string(input_data)}
        ).json()
        print(f"Response: {resp}. Latency {(time.time()-t0):.2f}s.")

    def add_labels(self, names: List[str]):
        endpoint = f"functions/{self.function_id}/labels"
        print(f"POSTing {len(names)} labels to [{requester_v1._get_full_url(endpoint)}]")
        for name in names:
            label_id = requester_v1.post(
                f"functions/{self.function_id}/labels", body={"name": name, "description": ""}
            ).json()["id"]
            self.label_name_to_id[name] = label_id

    def add_samples(self, samples: List[Sample]):
        endpoint = f"functions/{self.function_id}/samples"
        print(f"POSTing {len(samples)} samples to [{requester_v1._get_full_url(endpoint)}]")
        return Parallel(n_jobs=100, prefer="threads")(
            delayed(self._post_annotated_sample)(sample) for sample in tqdm(samples)
        )

    def add_image_folder(self, folder: str, label_name: str):
        image_suffix_list = ["JPG", "jpg", "JPEG", "jpeg", "PNG", "png"]
        image_list = []
        for image_suffix in image_suffix_list:
            image_list.extend(glob(os.path.join(f"{folder}/*.{image_suffix}")))
        self.add_samples([(entry, label_name) for entry in image_list])

    def _add_labels_for_all_samples(self, samples):
        label_names = list(set(sample[1] for sample in samples))
        if None in label_names:
            label_names.remove(None)
        print(f"Adding {len(label_names)} labels.")
        for label_name in label_names:
            self.add_label(label_name)

    def _post_annotated_sample(self, sample: Tuple[InputData, LabelName]):
        succeeded = False
        n_tries = 0
        while not succeeded and n_tries < 3:
            n_tries += 1
            try:
                resp = requester_v1.post(
                    f"functions/{self.function_id}/samples",
                    body=self._sample_to_payload(sample),
                )
                new_sample_id = resp.json()["id"]
                succeeded = True
            except Exception as e:
                print(f"Posting sample failed the {n_tries} attempt with {e}. Sleeping 5 secs.")
                time.sleep(5)
        if n_tries == 3:
            print("Gave up after 3 tries.")

        return new_sample_id

    def _sample_to_payload(self, sample: Tuple[InputData, LabelName]):
        input_data, label_name = sample
        if label_name is not None:
            payload = {
                "data": self._input_data_to_string(input_data),
                "annotation": {"labelId": self.label_name_to_id[label_name]},
            }
        else:
            payload = {
                "data": self._input_data_to_string(input_data),
            }
        return payload

    def _input_data_to_string(self, input_data):
        if self.modality == "Text":
            inline_data = input_data
        elif self.modality == "Image":
            if isinstance(input_data, str):
                image = Image.open(input_data)  # Try interpreting string as sa path
            elif isinstance(input_data, Image.Image):
                image = input_data
            inline_data = base64encoded_image(image)
        return inline_data

    @abstractmethod
    def _get_project_id():
        resp = requester_v09.get("projects").json()
        if len(resp) < 1:
            project_id = NyckelFunction._post_project()
        else:
            project_id = resp[0]["id"]
        return project_id

    @abstractmethod
    def _post_project():
        project_id = requester_v09.post("projects", body={"name": "Auto-gen", "admins": []}).json()["id"]
        return project_id

    @abstractmethod
    def _post_function(project_id, name, modality, description, is_public):
        function_id = requester_v09.post(
            "functions",
            body={
                "projectId": project_id,
                "name": name,
                "inputModality": modality,
                "description": description,
                "isPublic": is_public,
            },
        ).json()["id"]
        return function_id
