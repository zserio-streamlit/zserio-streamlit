import os
import shutil
import streamlit as st

from zipfile import ZipFile

from interactive_zserio.widget import Widget

class Uploader(Widget):
    def __init__(self, ws_dir, zs_dir):
        super().__init__("uploader")
        self._ws_dir = ws_dir
        self._zs_dir = zs_dir

    def render(self):
        self._log("render")
        upload_help="Upload either a simple schema file *.zs, or complex schema as a *.zip."
        uploaded_schema = st.file_uploader("Upload schema", type=["zs","zip"], help=upload_help,
                                           key=self._key("uploaded_schema"), on_change=self._on_change)
        if not uploaded_schema:
            st.stop()

    def _on_change(self):
        shutil.rmtree(self._zs_dir)
        os.makedirs(self._zs_dir)
        uploaded_schema = st.session_state[self._key("uploaded_schema")]
        if uploaded_schema:
            self._process_uploaded_file(uploaded_schema)

    def _process_uploaded_file(self, uploaded_file):
        if uploaded_file.name.endswith(".zs"):
            self._log("processing *.zs file:", uploaded_file.name)
            with open(os.path.join(self._zs_dir, uploaded_file.name), "wb") as zs_file:
                zs_file.write(uploaded_file.read())
        else:
            with ZipFile(uploaded_file, "r") as zip_file:
                if all(name.startswith(self._ws_dir) for name in zip_file.namelist()):
                    self._log("processing *.zip workspace file:", uploaded_file.name)
                    shutil.rmtree(self._ws_dir)
                    zip_file.extractall()
                else:
                    self._log("processing *.zip schema file:", uploaded_file.name)
                    zip_file.extractall(self._zs_dir)
