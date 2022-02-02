import os
import streamlit as st

from streamlit_ace import st_ace

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
            content = f.read()

        # changing the key causes the content change - i.e. change it for each file!
        # (whitout changing the key, assigning the old content won't affect the real content of the editor)
        # see https://github.com/okld/streamlit-ace/issues/28
        self._content = st_ace(content, key=self._key("content" + self._file_path), min_lines=12)
        if self._content != content:
            with open(os.path.join(self._root_dir, self._file_path), "w") as f:
                self._log("writing file:", self._file_path)
                f.write(self._content)

    @property
    def content(self):
        return self._content

