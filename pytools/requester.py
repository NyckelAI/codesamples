import os
import time

import requests
from typing import Dict

assert os.getenv("NYCKEL_CLIENT_ID"), "NYCKEL_CLIENT_ID env variable not set; can't setup connection."
assert os.getenv("NYCKEL_CLIENT_SECRET"), "NYCKEL_CLIENT_SECRET env variable not set; can't setup connection."


class Requester:
    """Class to talk to the Server. Manages the OAuth flow and retries in case connection is down."""

    def __init__(
        self,
        client_id: str = os.getenv("NYCKEL_CLIENT_ID"),
        client_secret: str = os.getenv("NYCKEL_CLIENT_SECRET"),
        host: str = "https://www.nyckel.com/",
        api_version: str = "v1.0",
        nbr_max_attempts=5,
        attempt_wait_sec=5,
    ):

        self.client_id = client_id
        self.client_secret = client_secret
        self.host = host
        self.api_version = api_version
        self._access_token = "Placeholder"
        self.nbr_max_attempts = nbr_max_attempts
        self.attempt_wait_sec = attempt_wait_sec

    def get(self, endpoint: str):
        return self._request_with_retries(requests.get, endpoint)

    def post(self, endpoint: str, body: Dict):
        return self._request_with_retries(requests.post, endpoint, json=body)

    def put(self, endpoint: str, body: Dict):
        return self._request_with_retries(requests.put, endpoint, json=body)

    def repeated_get(self, endpoint: str):
        resp = self.get(endpoint)
        resource_list = resp.json()
        while "next" in resp.links:
            endpoint = resp.links["next"]["url"]
            resp = self.get(endpoint)
            resource_list.extend(resp.json())
        return resource_list

    def _request_with_retries(self, request, endpoint, **kwargs):
        url = self._get_full_url(endpoint)
        attempt_counter = 0
        resp = None
        while not resp and attempt_counter < self.nbr_max_attempts:
            try:
                resp = self._request_with_renewal(request, url, **kwargs)
            except requests.exceptions.RequestException as err:
                print(f"RequestException at {url}: {err}.")
                time.sleep(self.attempt_wait_sec)
            attempt_counter += 1
        return resp

    def _request_with_renewal(self, request, url, **kwargs):

        kwargs["headers"] = {"authorization": "Bearer " + self._access_token}
        resp = request(url, **kwargs)
        if resp.status_code == 401:
            self._renew_access_token()
            kwargs["headers"] = {"authorization": "Bearer " + self._access_token}
            resp = request(url, **kwargs)

        if resp.status_code == 200:
            return resp
        else:
            raise RuntimeError(f"Call failed with {resp.status_code}: {resp.text}")

    def _renew_access_token(self):
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }
        token_url = self.host.rstrip("/") + "/connect/token"
        resp = requests.post(token_url, data=payload)
        if "access_token" not in resp.json():
            raise RuntimeError(f"Renewing access token failed with {resp.status_code}: {resp.text}")
        self._access_token = resp.json()["access_token"]

    def _get_full_url(self, endpoint):
        return self.host.rstrip("/") + "/v" + self.api_version.lstrip("v").rstrip("/") + "/" + endpoint.lstrip("/")
