import streamlit as st
import subprocess
import sys

from interactive_zserio.widget import Widget
from interactive_zserio.file_manager import FileManager
from interactive_zserio.editor import Editor

class PythonRunner(Widget):
    def __init__(self, python_gen_dir, src_dir):
        super().__init__("python_runner")
        self._python_gen_dir = python_gen_dir
        self._src_dir = src_dir

        self._python_file_manager = FileManager("python_file_manager", self._src_dir, "py")
        self._python_editor = Editor("python_editor", self._src_dir, lang="python")

        self._python_generated = None

    def set_python_generated(self, python_generated):
        self._python_generated = python_generated

    @property
    def check(self):
        return st.session_state[self._key("check")]

    @check.setter
    def check(self, value):
        st.session_state[self._key("check")] = value

    def render(self):
        self._log("render")

        st.checkbox("Experimental python code", key=self._key("check"),
                                          disabled=(not self._python_generated),
                                          help="Python generator must be enabled")
        if not st.session_state[self._key("check")] or not self._python_generated:
            return

        self._python_file_manager.render()

        self._python_editor.set_file(self._python_file_manager.selected_file)
        self._python_editor.render()

        self._log("executing code:", self._python_file_manager.selected_file)

        try:
            completed_process = subprocess.run(
                [sys.executable, "-c", self._python_editor.content],
                cwd=self._python_gen_dir,
                env={
                    "PYTHONDONTWRITEBYTECODE" : "1"
                },
                capture_output=True, text=True,
                timeout=5
            )

            st.caption("Python output")
            if completed_process.stdout:
                st.text(completed_process.stdout)
            if completed_process.stderr:
                st.error(completed_process.stderr)
        except subprocess.TimeoutExpired as e:
            st.error(f"{e.timeout}s timeout expired!")
        except Exception as e:
            st.error(e)
