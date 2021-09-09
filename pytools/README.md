# PYTOOLS

## Setup

(These codesamples are only tested on `python3.7`)

```bash
pip install -r requirements.txt
```

Navigate to the API page of a function you already created and set local env variables:

```bash
export NYCKEL_CLIENT_SECRET=...
export NYCKEL_CLIENT_ID=...
```

## Run

Note down the function id for a function you already created. It's in the URL. Then run the download script like so. This downloads some function meta-data and all samples to a folder in this directory.

```bash
python download_function.py <your_function_id>
```

Then run the upload script to create a new function from the data you just downloaded.

```bash
python upload_function.py <your_function_id>
```
