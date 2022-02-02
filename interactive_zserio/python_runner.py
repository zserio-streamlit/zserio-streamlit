import os
import streamlit as st
import sys

from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

from interactive_zserio.widget import Widget
from interactive_zserio.file_manager import FileManager
from interactive_zserio.editor import Editor

class PythonRunner(Widget):
    def __init__(self, python_gen_dir, src_dir):
        super().__init__("python_runner")
        self._python_gen_dir = python_gen_dir
        self._src_dir = src_dir

        self._python_file_manager = FileManager("python_file_manager", self._src_dir, "py")
        self._python_editor = Editor("python_editor", self._src_dir)

    def render(self):
        self._log("render")

        self._python_file_manager.render()

        self._python_editor.set_file(self._python_file_manager.selected_file)
        self._python_editor.render()

        sys.dont_write_bytecode = True
        if sys.path[-1] != self._python_gen_dir:
            sys.path.append(self._python_gen_dir)

        modules_keys = set(sys.modules.keys())

        with StringIO() as out, redirect_stdout(out):
            st.caption("Python output")
            try:
                self._log("executing code:", self._python_file_manager.selected_file)
                exec(self._python_editor.content)
                st.text(out.getvalue())
            except Exception as e:
                st.text(out.getvalue())
                st.error(e)

        # allow to reload modules imported by the python code
        new_modules_keys = set(sys.modules.keys())
        modules_to_remove = new_modules_keys - modules_keys
        for module_to_remove in modules_to_remove:
            sys.modules.pop(module_to_remove)
