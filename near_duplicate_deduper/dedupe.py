import glob
import os

import fire
import time

from near_duplicate_deduper import NyckelNearDuplicateDeduper

COMMON_IMAGE_EXTENSIONS = ["jpg", "png", "jpeg", "JPG", "JPEG", "PNG"]


def main(client_id: str, client_secret: str, folder: str, max_nbr_file_to_dedupe: int = 10):
    image_filelist = []
    for image_extension in COMMON_IMAGE_EXTENSIONS:
        image_filelist.extend(glob.glob(os.path.join(folder, f"*.{image_extension}")))
    image_filelist = image_filelist[:max_nbr_file_to_dedupe]

    t0 = time.time()
    duplicate_clusters = NyckelNearDuplicateDeduper(client_id, client_secret).dedupe_filelist(image_filelist)
    runtime = time.time() - t0

    print("----")
    print(f"Deduped {len(image_filelist)} images in {runtime} seconds.")
    print(f"Found {len(duplicate_clusters)} clusters of duplicates")
    for cluster in duplicate_clusters:
        print(f"Cluster1: {cluster}")


if __name__ == "__main__":
    fire.Fire(main)
