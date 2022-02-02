import os
import streamlit as st

from interactive_zserio.widget import Widget

class Editor(Widget):
    def __init__(self, name, root_dir):
        super().__init__(name)
        self._root_dir = root_dir

        self._file_path = None
        self._content = None

    def set_file(self, file_path):
        self._file_path = file_path

    def render(self):
        self._log("render")
        with open(os.path.join(self._root_dir, self._file_path), "r") as f:
            self._log("reading file:", self._file_path)
            st.session_state[self._key("file_content")] = f.read()

        st.text_area(self._file_path, height=250, key=self._key("file_content"), on_change=self._on_change)

        self._content = st.session_state[self._key("file_content")]

    @property
    def content(self):
        return self._content

    def _on_change(self):
        with open(os.path.join(self._root_dir, self._file_path), "w") as f:
            self._log("writing file:", self._file_path)
            f.write(st.session_state[self._key("file_content")])
