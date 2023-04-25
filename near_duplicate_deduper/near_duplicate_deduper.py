import base64
import concurrent.futures
import time
from io import BytesIO
from typing import List, Set, Tuple

import requests
from PIL import Image

IMAGE_SIZE_FOR_POSTING = [224, 224]


def base64encoded_image(img: Image, format="JPEG"):
    """
    Converts a PIL Image to a base64-encoded string.
    """
    buffered = BytesIO()
    if not img.mode == "RGB":
        img = img.convert("RGB")
    img.save(buffered, format=format)
    encoded_string = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return "data:image/jpg;base64," + encoded_string


class NyckelNearDuplicateDeduper:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        duplication_threshold: float = 0.05,
        max_nbr_concurrent_requests: int = 20,
    ):
        """
        Initializes a new instance of the NyckelNearDuplicateDeduper class.

        client_id: The Nyckel client ID.
        client_secret: The Nyckel client secret.
        duplication_threshold: The threshold above which two images are not considered duplicates.
        max_nbr_concurrent_requests: The maximum number of concurrent requests to the Nyckel function.
        """
        self._client_id: str = client_id
        self._client_secret: str = client_secret
        self._duplication_threshold = duplication_threshold
        self._max_nbr_concurrent_requests = max_nbr_concurrent_requests
        self._function_id: str
        self._session = requests.Session()

    def dedupe_filelist(self, image_filelist: List[str]) -> List[Set[str]]:
        """
        Deduplicates a list of image files using the Nyckel near-duplicate search API.

        image_filelist: A list of image file paths.

        Returns a list of sets, where each set contains the file paths of duplicate images.
        """
        self._initialize_session()
        self._create_function()
        sample_ids_by_filename = self._post_images(image_filelist)
        similarity_by_filename = self._search_images(image_filelist)
        duplicate_pairs = self._get_duplicate_pairs(sample_ids_by_filename, similarity_by_filename)
        duplicate_clusters = DuplicateClusterIdentifier()(duplicate_pairs)
        self._delete_function()
        return duplicate_clusters

    def _initialize_session(self):
        """
        Gets an access token from Nyckel using the client ID and secret.
        """
        token_url = "https://www.nyckel.com/connect/token"

        data = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "grant_type": "client_credentials",
        }

        response = requests.post(token_url, data=data)
        assert response.status_code == 200, f"Something went wrong when getting access token: {response.text}"
        access_token = response.json()["access_token"]
        self._session.headers.update({"authorization": "Bearer " + access_token})

    def _create_function(self):
        """
        Creates a new Nyckel function to use for near-duplicate search.
        """
        print("Creating function to use for deduplication ...")

        def _strip_prefix(prefixed_function_id):
            return prefixed_function_id[9:]

        response = self._session.post(
            "https://www.nyckel.com/v1/functions/", json={"input": "Image", "output": "Search"}
        )

        assert response.status_code == 200, f"Something went wrong when creating function: {response.text}"
        prefixed_function_id = response.json()["id"]
        self._function_id = _strip_prefix(prefixed_function_id)

    def _post_images(self, image_filelist: List[str]):
        """
        Posts images to the Nyckel function.

        image_filelist: A list of image file paths to post.

        Returns a dictionary mapping sample IDs to file names.
        """
        print(f"Posting images to function {self._function_id}...")
        t0 = time.time()
        filename_by_sample_id = {}
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(len(image_filelist), self._max_nbr_concurrent_requests)
        ) as executor:
            filename_by_futures = {
                executor.submit(self._post_one_image, img_file): img_file for img_file in image_filelist
            }
            for future in concurrent.futures.as_completed(filename_by_futures):
                img_file = filename_by_futures[future]
                filename_by_sample_id[future.result()] = img_file

        runtime = time.time() - t0
        print(f"Posted {len(image_filelist)} images in {runtime} seconds.")
        return filename_by_sample_id

    def _search_images(self, image_filelist: List[str]):
        """
        Searches for near-duplicate images using the Nyckel function.

        image_filelist: A list of image file paths to search.

        Returns a dictionary mapping file names to near-duplicate search results.
        """
        print(f"Searching images in function {self._function_id}...")
        t0 = time.time()
        similarity_by_filename = {}
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(len(image_filelist), self._max_nbr_concurrent_requests)
        ) as executor:
            filename_by_futures = {
                executor.submit(self._find_closest_match_excluding_self, img_file): img_file
                for img_file in image_filelist
            }
            for future in concurrent.futures.as_completed(filename_by_futures):
                img_file = filename_by_futures[future]
                similarity_by_filename[img_file] = future.result()

        runtime = time.time() - t0
        print(f"Searched {len(image_filelist)} images in {runtime} seconds.")
        return similarity_by_filename

    def _get_duplicate_pairs(self, filename_by_sample_id, similarity_by_filename):
        """
        Gets a list of duplicate pairs from the near-duplicate search results.

        filename_by_sample_id: A dictionary mapping sample IDs to file names.
        similarity_by_filename: A dictionary mapping file names to near-duplicate search results.

        Returns a list of duplicate pairs, where each pair is a set containing the file names of two duplicate images.
        """
        duplicate_pairs: List[Set[str, str]] = []
        for filename in similarity_by_filename:
            if similarity_by_filename[filename]["distance"] < self._duplication_threshold:
                duplicate_pairs.append(
                    set([filename, filename_by_sample_id[similarity_by_filename[filename]["sampleId"]]])
                )
        return duplicate_pairs

    def _delete_function(self):
        """
        Deletes the Nyckel function after use.
        """
        response = self._session.delete(f"https://www.nyckel.com/v1/functions/{self._function_id}")
        assert response.status_code == 200, "Error during cleanup (deleting function f{self._functionid})"

    def _post_one_image(self, img_file_path: str):
        """
        Posts a single image to the Nyckel function and returns its sample ID.

        img_file_path: The file path of the image to post.

        Returns the sample ID of the posted image.
        """
        img = Image.open(img_file_path)
        img = img.resize(IMAGE_SIZE_FOR_POSTING)
        response = self._session.post(
            f"https://www.nyckel.com/v1/functions/{self._function_id}/samples",
            json={"data": base64encoded_image(img)},
        )
        assert response.status_code in [
            200,
            409,
        ], f"Something went wrong when posting {img_file_path=} {response.text=} {response.status_code=}"
        return response.json()["id"]

    def _find_closest_match_excluding_self(self, img_file_path: str):
        """
        Finds the closest match to an image, excluding itself, using the Nyckel function.

        img_file_path: The file path of the image to search.

        Returns the near-duplicate search result of the closest match to the image, excluding itself.
        """
        img = Image.open(img_file_path)
        img = img.resize(IMAGE_SIZE_FOR_POSTING)
        response = self._session.post(
            f"https://www.nyckel.com/v0.9/functions/{self._function_id}/search?sampleCount=2",
            json={"data": base64encoded_image(img)},
        )
        assert response.status_code == 200, f"Something went wrong when searching {img_file_path=} {response.text=}"
        return response.json()["searchSamples"][1]


class DuplicateClusterIdentifier:
    def __init__(self):
        self.clusters: List[Set[str]] = []

    def __call__(self, duplicate_pairs: List[Tuple[str, str]]) -> List[Set[str]]:
        """
        Identifies clusters of near-duplicate images from a list of duplicate pairs.

        duplicate_pairs: A list of duplicate pairs, where each pair is a tuple containing the file names of two duplicate images.

        Returns a list of duplicate clusters, where each cluster is a set containing the file names of near-duplicate images.
        """
        for member1, member2 in duplicate_pairs:
            if not self._is_in_any_cluster(member1) and not self._is_in_any_cluster(member2):
                "Not seen these entries before. Create a new cluster"
                self._create_new_cluster(member1, member2)

            if self._is_in_any_cluster(member1) and self._is_in_any_cluster(member2):
                "Both are in clusters. Merge them. Merge will ignore if the clusters are the same"
                self._merge_clusters(self._get_cluster(member1), self._get_cluster(member2))

            if self._is_in_any_cluster(member1) and not self._is_in_any_cluster(member2):
                "Member1 is in a cluster, but not member2, Add member2 to member1's cluster"
                self._add_to_cluster(member2, self._get_cluster(member1))

            if self._is_in_any_cluster(member2) and not self._is_in_any_cluster(member1):
                "Member2 is in a cluster, but not member1, Add member1 to member2's cluster"
                self._add_to_cluster(member1, self._get_cluster(member2))

        self._remove_empty_clusters()

        return self.clusters

    def _is_in_any_cluster(self, member: str):
        """
        Checks if an image is in any cluster.

        member: The file name of the image to check.

        Returns True if the image is in any cluster, False otherwise.
        """
        for cluster in self.clusters:
            if member in cluster:
                return True
        return False

    def _get_cluster(self, member: str):
        """
        Gets the cluster of an image.

        member: The file name of the image to get the cluster of.

        Returns the cluster that the image is in.
        """
        for cluster in self.clusters:
            if member in cluster:
                return cluster
        raise ValueError("Cant get cluster for {member} -- not in any cluster")

    def _create_new_cluster(self, member1, member2):
        """
        Creates a new cluster for two near-duplicate images.

        member1: The file name of the first image.
        member2: The file name of the second image.
        """
        self.clusters.append(set([member1, member2]))

    def _merge_clusters(self, cluster1, cluster2):
        """
        Merges two clusters.

        cluster1: The first cluster.
        cluster2: The second cluster.
        """
        if cluster1 == cluster2:
            return
        cluster2_members = list(cluster2)
        for member in cluster2_members:
            cluster1.add(member)
            cluster2.remove(member)

    def _add_to_cluster(self, member, cluster):
        """
        Adds an image to a cluster.

        member: The file name of the image to add.
        cluster: The cluster to add the image to.
        """
        cluster.add(member)

    def _remove_empty_clusters(self):
        """
        Removes empty clusters from the list of clusters.
        """
        clusters_tmp = []

        for cluster in self.clusters:
            if len(cluster) > 0:
                clusters_tmp.append(cluster)
        self.clusters = clusters_tmp
