import os
import streamlit as st

from zipfile import ZipFile

from interactive_zserio.widget import Widget

class Downloader(Widget):
    def __init__(self, name, root, folder, zip_name, zip_folder=None, *, label=None, help=None,
                 exclude_extensions=None):
        super().__init__(name)

        self._root = root
        self._folder = folder
        self._zip_name = zip_name
        self._zip_folder = zip_folder if zip_folder is not None else folder
        self._label = label if label is not None else "Download"
        self._help = help
        self._exclude_extensions = exclude_extensions if exclude_extensions is not None else []

    def render(self):
        self._log("render")

        zip_path = os.path.join(self._folder, self._zip_name)
        if os.path.exists(zip_path):
            os.remove(zip_path)

        files_to_zip = []
        for root, _, files in os.walk(self._folder):
            for f in files:
                if not any(f.endswith("*." + ext) for ext in self._exclude_extensions):
                    files_to_zip.append(os.path.join(root, f))
        with ZipFile(zip_path, "w") as zip_file:
            for f in files_to_zip:
                zip_file.write(f, os.path.relpath(f, self._root))

        with open(zip_path, "rb") as zip_file:
            st.download_button(self._label, zip_file, mime="application/zip", help=self._help)
