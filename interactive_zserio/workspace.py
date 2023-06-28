import os
import shutil

from interactive_zserio.widget import Widget

class Workspace(Widget):
    def __init__(self, ws_dir):
        super().__init__("workspace")
        self._ws_dir = ws_dir
        self._zs_dir = os.path.join(self._ws_dir, "zs")
        self._gen_dir = os.path.join(self._ws_dir, "gen")
        self._src_dir = os.path.join(self._ws_dir, "src")
        self.create()

    @property
    def ws_dir(self):
        return self._ws_dir

    @property
    def zs_dir(self):
        return self._zs_dir

    @property
    def gen_dir(self):
        return self._gen_dir

    @property
    def src_dir(self):
        return self._src_dir

    def create(self):
        os.makedirs(self._ws_dir, exist_ok=True)
        os.makedirs(self._zs_dir, exist_ok=True)
        os.makedirs(self._gen_dir, exist_ok=True)
        os.makedirs(self._src_dir, exist_ok=True)

    def clear(self):
        shutil.rmtree(self._ws_dir, ignore_errors=True)

    def reset(self):
        self.clear()
        self.create()

    def load_json(self, json):
        self._log("loading json")

        try:
            for src in json["zs"]:
                with open(os.path.join(self._zs_dir, src["name"]), "w") as f:
                    f.write(src["content"])

            if "src" in json and "python" in json["src"]:
                python_dir = os.path.join(self._src_dir, "python")
                os.makedirs(python_dir, exist_ok=True)
                for src in json["src"]["python"]:
                    with open(os.path.join(python_dir, src["name"]), "w") as f:
                        f.write(src["content"])
        except Exception as e:
            self._log("loading json failed:", type(e), e)
            return False

        return True

    def use_sample_fallback(self):
        self._log("using sample fallback")
        self.clear()
        shutil.copytree("sample_workspace", self._ws_dir)

    def get_json(self):
        ws_json = {"zs": [], "src": {}}

        for root, _, files in os.walk(self._zs_dir):
            for name in files:
                with open(os.path.join(root, name)) as f:
                    ws_json["zs"].append({"name": name, "content": f.read()})

        python_dir = os.path.join(self._src_dir, "python")
        if os.path.exists(python_dir):
            ws_json["src"]["python"] = []
            for root, _, files in os.walk(python_dir):
                for name in files:
                    with open(os.path.join(root, name)) as f:
                        ws_json["src"]["python"].append({"name": name, "content": f.read()})

        return ws_json
