import os
import streamlit as st
import sys

from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

from interactive_zserio.widget import Widget
from interactive_zserio.editor import Editor

class PythonRunner(Widget):
    def __init__(self, python_gen_dir, src_dir):
        super().__init__("python_runner")
        self._python_gen_dir = python_gen_dir
        self._src_dir = src_dir

    def render(self):
        self._log("render")

        code_file_path = os.path.join(self._src_dir, self.CODE_FILENAME)
        if not os.path.exists(code_file_path):
            open(code_file_path, "w").close()

        sys.dont_write_bytecode = True
        if sys.path[-1] != self._python_gen_dir:
            sys.path.append(self._python_gen_dir)

        modules_keys = set(sys.modules.keys())

        python_editor = Editor("python_editor", self._src_dir, self.CODE_FILENAME)
        python_editor.render()

        with StringIO() as out, redirect_stdout(out):
            st.caption("Python output")
            try:
                exec(python_editor.content)
                st.text(out.getvalue())
            except Exception as e:
                st.error(e)

        # allow to reload modules imported by the python code
        new_modules_keys = set(sys.modules.keys())
        modules_to_remove = new_modules_keys - modules_keys
        for module_to_remove in modules_to_remove:
            sys.modules.pop(module_to_remove)

    CODE_FILENAME = "code.py"
