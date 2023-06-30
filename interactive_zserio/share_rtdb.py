import os
import requests
import uuid
import json

from http import HTTPStatus
from datetime import datetime

from interactive_zserio.widget import Widget

class ShareRTDB(Widget):
    def __init__(self, workspace, generator, python_runner):
        super().__init__("share")
        self._workspace = workspace
        self._generator = generator
        self._python_runner = python_runner

    def restore_sample(self):
        with open("sample.json") as f:
            self._restore_json(json.loads(f.read()))

    def restore(self, share_id):
        self._log("loading shared workspace:", share_id)
        response = requests.get(FIREBASE_RTDB + "user_workspaces/" + share_id + ".json",
                                params={"auth": os.getenv('AUTH_TOKEN')})
        self._log("getting shared workspace from RTDB, status:", response.status_code)
        return response.status_code == HTTPStatus.OK and self._restore_json(response.json())

    def _restore_json(self, shared_json):
        if shared_json is not None:
            try:
                ws_json = shared_json["ws"]
                if not self._workspace.load_json(ws_json):
                    return False
                self._generator.set_state(shared_json["generator"])
                self._python_runner.check = shared_json["python_runner"]
                return True
            except Exception as e:
                self._log("failed to parse shared json:", type(e), e)
        else:
            self._log("shared workspace does not exists:", share_id)
        return False

    def delete_old_shares(self):
        self._log("deleting old shares")
        response = requests.get(FIREBASE_RTDB + "user_dates.json",
                                params={"auth": os.getenv('AUTH_TOKEN')})
        if response.status_code == HTTPStatus.OK:
            dates_json = response.json()
            if dates_json is None:
                return

            today = datetime.now().date()
            deletes = {
                k: None for k, v in dates_json.items() if
                (today - datetime.fromisoformat(v).date()).days > DAYS_LIMIT
            }

            result = requests.patch(FIREBASE_RTDB + "user_workspaces.json",
                                    params={"auth": os.getenv('AUTH_TOKEN')},
                                    json=deletes)
            if result.status_code != HTTPStatus.OK:
                self._log("failed to delete old workspaces")

            result = requests.patch(FIREBASE_RTDB + "user_dates.json",
                                    params={"auth": os.getenv('AUTH_TOKEN')},
                                    json=deletes)
            if result.status_code != HTTPStatus.OK:
                self._log("failed to delete old dates")

    def share(self, share_id):
        self._log("sharing workspace via RTDB as:", share_id)

        result = requests.put(FIREBASE_RTDB + "user_dates/" + share_id + ".json",
                              params={"auth": os.getenv('AUTH_TOKEN')},
                              json=datetime.now().date().isoformat())
        if result.status_code != HTTPStatus.OK:
            self._log("sharing workspace via RTDB failed:", result.status_code)
            return False

        result = requests.put(FIREBASE_RTDB + "user_workspaces/" + share_id + ".json",
                              params={"auth": os.getenv('AUTH_TOKEN')},
                              json=self._get_json())
        if result.status_code != HTTPStatus.OK:
            self._log("sharing workspace via RTDB failed:", result.status_code)
            return False

        return True

    def _get_json(self):
        return {
            "ws": self._workspace.get_json(),
            "generator": self._generator.get_state(),
            "python_runner": self._python_runner.check
        }

    @staticmethod
    def new_id():
        return uuid.uuid1().hex

FIREBASE_RTDB="https://interactive-zserio-default-rtdb.europe-west1.firebasedatabase.app/"
DAYS_LIMIT=365
