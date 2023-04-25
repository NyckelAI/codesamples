# Near Duplicate DeDuper

A simple python CLI that uses the Nyckel Image Search function type to deduplicate a set of images.

See <https://www.nyckel.com/docs/near-duplicate-removal> for more context.

## Installation

* Create a new virtual environment
* Run `pip install -r requirements.txt`

## Create Nyckel accounts

* Create account at <https://www.nyckel.com/>
* Go to <https://www.nyckel.com/console/keys> and note the `Client Id` and `Client Secret`

## Run program

```python
python -m main <nyckel_client_id> <nyckel_secret_id> <path_to_folder_with_image_files>
```
