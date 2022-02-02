import os
import shutil
import streamlit as st

from zipfile import ZipFile

from interactive_zserio.widget import Widget
from interactive_zserio.uploader import Uploader
from interactive_zserio.file_manager import FileManager
from interactive_zserio.editor import Editor
from interactive_zserio.generator import Generator
from interactive_zserio.sources_viewer import SourcesViewer
from interactive_zserio.python_runner import PythonRunner

class MainView(Widget):
    def __init__(self):
        super().__init__("main_view")
        self._ws_dir = "workspace"
        self._zs_dir = os.path.join(self._ws_dir, "zs")
        self._gen_dir = os.path.join(self._ws_dir, "gen")
        self._src_dir = os.path.join(self._ws_dir, "src")
        self._zip_filename = "workspace.zip"

        self._uploader = Uploader(self._ws_dir, self._zs_dir)
        self._schema_file_manager = FileManager("schema_file_manager", self._zs_dir, "zs",
                                                self._new_schema_file_callback)
        self._schema_editor = Editor("schema_editor", self._zs_dir)
        self._generator = Generator(self._zs_dir, self._gen_dir)
        self._sources_viewer = SourcesViewer(self._gen_dir)

        self._python_runner = PythonRunner(os.path.join(self._gen_dir, "python"),
                                           os.path.join(self._src_dir, "python"))

        if self._key("schema_mode") not in st.session_state:
            # initialize on the first run or after refresh (F5)
            st.session_state[self._key("schema_mode")] = "sample"
            self._schema_mode_on_change()

    def render(self):
        self._log("render")
        st.set_page_config(layout="wide", page_title="Interactive Zserio", page_icon="./img/zs.png")

        st.write("""
            # Interactive Zserio Compiler!
        """)

        schema_modes = { "write": "Write schema", "upload": "Upload schema or workspace", "sample": "Sample" }
        schema_mode = st.selectbox("Schema", schema_modes, format_func=lambda x: schema_modes[x],
                                   key=self._key("schema_mode"), on_change=self._schema_mode_on_change)
        if schema_mode == "upload":
            self._uploader.render()

        self._schema_file_manager.render()

        self._schema_editor.set_file(self._schema_file_manager.selected_file)
        self._schema_editor.render()

        self._generator.set_zs_file_path(self._schema_file_manager.selected_file)
        self._generator.render()

        self._sources_viewer.set_generators(self._generator.generators)
        self._sources_viewer.render()

        python_code_check = st.checkbox("Experimental python code", value=True,
                                        help="Python generator must be enabled")
        if python_code_check and self._generator.generators["python"]:
            self._python_runner.render()

        self._compress_ws()

    def _compress_ws(self):
        zip_path = os.path.join(self._ws_dir, self._zip_filename)
        if os.path.exists(zip_path):
            os.remove(zip_path)

        files_to_zip = []
        for root, _, files in os.walk(self._ws_dir):
            for f in files:
                files_to_zip.append(os.path.join(root, f))
        with ZipFile(zip_path, "w") as zip_file:
            for f in files_to_zip:
                zip_file.write(f)

        with open(zip_path, "rb") as zip_file:
            st.download_button("Download workspace", zip_file, mime="application/zip",
                               help="Download whole workspace as a zip file.")

    def _new_schema_file_callback(self, folder, file_path):
        package_definition = ".".join(os.path.splitext(file_path)[0].split(os.sep))
        self._log("new schema file:", package_definition)
        with open(os.path.join(folder, file_path), "w") as new_file:
            new_file.write(f"package {package_definition};\n")

    def _schema_mode_on_change(self):
        self._generator.reset()

        shutil.rmtree(self._ws_dir, ignore_errors=True)

        if st.session_state[self._key("schema_mode")] == "sample":
            shutil.copytree("sample_workspace", self._ws_dir)

        os.makedirs(self._ws_dir, exist_ok=True)
        os.makedirs(self._zs_dir, exist_ok=True)
        os.makedirs(self._gen_dir, exist_ok=True)
        os.makedirs(self._src_dir, exist_ok=True)
